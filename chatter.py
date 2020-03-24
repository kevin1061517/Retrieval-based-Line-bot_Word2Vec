#!/usr/bin/env python
# coding: utf-8

import torch.nn as nn
import torch.nn.init as init
from torch.utils.data import Dataset, DataLoader
from torch import optim
import torch.nn.functional as F
from gensim.models import Word2Vec
import random
import pdb
import numpy as np
import torch
import jieba as jb
import math
import time
import pickle

MAXLEN = 20

def position_encoding_init(n_position, d_pos_vec):
    ''' Init the sinusoid position encoding table '''
    # keep dim 0 for padding token position encoding zero vector
    position_enc = np.array([
        [pos / np.power(10000, 2 * (j // 2) / d_pos_vec) for j in range(d_pos_vec)]
        if pos != 0 else np.zeros(d_pos_vec) for pos in range(n_position)])

    position_enc[1:, 0::2] = np.sin(position_enc[1:, 0::2]) # dim 2i
    position_enc[1:, 1::2] = np.cos(position_enc[1:, 1::2]) # dim 2i+1
    return torch.from_numpy(position_enc).type(torch.FloatTensor)
def get_attn_padding_mask(seq_q, seq_k):
    ''' Indicate the padding-related part to mask '''
    assert seq_q.dim() == 2 and seq_k.dim() == 2
    mb_size, len_q = seq_q.size()
    mb_size, len_k = seq_k.size()
    pad_attn_mask = seq_k.data.eq(2).unsqueeze(1)   # bx1xsk
    pad_attn_mask = pad_attn_mask.expand(mb_size, len_q, len_k) # bxsqxsk
    return pad_attn_mask

def get_attn_subsequent_mask(seq):
    ''' Get an attention mask to avoid using the subsequent info.'''
    assert seq.dim() == 2
    attn_shape = (seq.size(0), seq.size(1), seq.size(1))
    subsequent_mask = np.triu(np.ones(attn_shape), k=1).astype('uint8')
    subsequent_mask = torch.from_numpy(subsequent_mask)
    if seq.is_cuda:
        subsequent_mask = subsequent_mask.cuda()
    return subsequent_mask

class LayerNorm(nn.Module):
    def __init__(self, hidden_size):
        super(LayerNorm, self).__init__()
        self.a = nn.Parameter(torch.ones(hidden_size))
        self.b = nn.Parameter(torch.zeros(hidden_size))
        self.eps = 1e-6
    def forward(self, x):
        mu = x.mean(-1, keepdim=True)
        sigma = x.std(-1, keepdim=True)
        output = self.a * (x - mu) / (sigma) + self.b
        return output

class ScaledDotProductAttn(nn.Module):
    def __init__(self, hidden_size):
        super(ScaledDotProductAttn, self).__init__()
        self.scaler = hidden_size ** 0.5
    def forward(self, q, k, v, attn_mask=None):
        # batch, qlen, d_head * batch, d_head, klen
        attn_weight = torch.bmm(q, k.transpose(1,2)) / self.scaler
        if attn_mask is not None:
            attn_weight.data.masked_fill_(attn_mask, -float('inf'))
        # batch, qlen, klen
        attn_weight = F.softmax(attn_weight, dim=2)
        attn_weight = torch.bmm(attn_weight, v)
        return attn_weight

class MultiHeadAttn(nn.Module):
    def __init__(self, hidden_size, n_head=8):
        super(MultiHeadAttn, self).__init__()
        self.hidden_size = hidden_size
        self.n_head = n_head
        self.d_head = int(hidden_size / n_head)
        self.linears = nn.ModuleList([
            nn.Linear(hidden_size, hidden_size) for _ in range(4)
        ])
        [init.xavier_normal_(ll.weight) for ll in self.linears]
        self.attn = ScaledDotProductAttn(hidden_size)
        self.dropout = nn.Dropout(0.1)
        self.layer_norm = LayerNorm(hidden_size)
    def forward(self, q, k, v, attn_mask=None):
        batch_size, len_q, _ = q.size()
        len_k = k.size(1)
        # batch, qlen, emb_size
        residual = q
        qs, ks, vs = \
            [l(x).view(batch_size, -1, self.n_head, self.d_head).transpose(1, 2) \
             for l, x in zip(self.linears, (q, k, v))]
        qs = qs.contiguous().view(-1, len_q, self.d_head)
        ks = ks.contiguous().view(-1, len_k, self.d_head)
        vs = vs.contiguous().view(-1, len_k, self.d_head)        
        # SDP attn: batch*n_head, seqlen, d_head
        outputs = self.attn(qs, ks, vs, attn_mask.repeat(self.n_head,1,1))
        # concat: batch, seqlen, hidden_size
        outputs = outputs.view(-1, self.n_head, len_q, self.d_head).transpose(1,2)\
                        .contiguous().view(-1, len_q, self.n_head*self.d_head)
        outputs = self.linears[-1](outputs)
        return self.layer_norm(residual + self.dropout(outputs))

class PositionWiseDense(nn.Module):
    def __init__(self, hidden_size):
        super(PositionWiseDense, self).__init__()
        self.fc1 = nn.Linear(hidden_size, hidden_size*4)
        self.fc2 = nn.Linear(hidden_size*4, hidden_size)
        self.dropout = nn.Dropout(0.1)
        self.layer_norm = LayerNorm(hidden_size)
    def forward(self, x):
        residual = x
        output = self.fc2(F.relu(self.fc1(x)))
        return self.layer_norm(residual + self.dropout(output))

class EncodeSubLayer(nn.Module):
    def __init__(self, hidden_size):
        super(EncodeSubLayer, self).__init__()
        self.multi_head_attn = MultiHeadAttn(hidden_size)
        self.pos_wise_fc = PositionWiseDense(hidden_size)
    def forward(self, enc_input, slf_attn_mask=None):
        output = self.multi_head_attn(enc_input, enc_input, enc_input, slf_attn_mask)
        output = self.pos_wise_fc(output)
        return output

class DecodeSubLayer(nn.Module):
    def __init__(self, hidden_size):
        super(DecodeSubLayer, self).__init__()
        self.multi_head_attn = MultiHeadAttn(hidden_size)
        self.enc_attn = MultiHeadAttn(hidden_size)
        self.pos_wise_fc = PositionWiseDense(hidden_size)
    def forward(self, dec_input, enc_output, slf_attn_mask=None, ende_attn_padding_mask=None):
        dec_output = self.multi_head_attn(dec_input, dec_input, dec_input, slf_attn_mask)
        dec_output = self.enc_attn(dec_output, enc_output, enc_output, ende_attn_padding_mask)
        dec_output = self.pos_wise_fc(dec_output)
        return dec_output

class Encoder(nn.Module):
    def __init__(self, embedding_size, emb_weight, hidden_size):
        super(Encoder, self).__init__()
        self.n_pos = MAXLEN + 3
        self.hidden_size = hidden_size
        self.pos_enc = nn.Embedding(self.n_pos, embedding_size)
        self.pos_enc.weight.data = position_encoding_init(self.n_pos, embedding_size)
        self.seq_embedding = nn.Embedding.from_pretrained(emb_weight, freeze=False)
        self.dropout = nn.Dropout(p=0.1)
        self.layers = nn.ModuleList([
            EncodeSubLayer(hidden_size) for _ in range(6)
        ])

    def forward(self, src):
        seq, pos = src[:,:,0], src[:,:,1]
        slf_attn_padding_mask = get_attn_padding_mask(seq, seq)
        enc_input = self.seq_embedding(seq)
        pos_emb = self.pos_enc(pos)
        enc_input += pos_emb
        enc_output = self.dropout(enc_input)
        for layer in self.layers:
            enc_output = layer(enc_output, slf_attn_mask=slf_attn_padding_mask)
        return enc_output

class Decoder(nn.Module):
    def __init__(self, embedding_size, emb_weight, hidden_size, vocab_size):
        super(Decoder, self).__init__()
        self.n_pos = MAXLEN + 2
        self.hidden_size = hidden_size
        self.pos_enc = nn.Embedding(self.n_pos, embedding_size)
        self.pos_enc.weight.data = position_encoding_init(self.n_pos, embedding_size)
        self.seq_embedding = nn.Embedding.from_pretrained(emb_weight, freeze=False)
        self.layers = nn.ModuleList([
            DecodeSubLayer(hidden_size) for _ in range(6)
        ])
        self.dropout = nn.Dropout(p=0.1)
        self.output_layer = nn.Linear(hidden_size, vocab_size)
        self.softmax = nn.LogSoftmax(dim=2)

    def forward(self, target, enc_output, src):
        seq, pos = target[:,:self.n_pos-1,0], target[:,:self.n_pos-1,1]
        
        slf_attn_padding_mask = get_attn_padding_mask(seq, seq)
        slf_attn_sub_mask = get_attn_subsequent_mask(seq)
        slf_attn_mask = torch.gt(slf_attn_padding_mask + slf_attn_sub_mask, 0)
        ende_attn_padding_mask = get_attn_padding_mask(seq, src[:,:,0])
        
        dec_input = self.seq_embedding(seq)
        pos_emb = self.pos_enc(pos)
        dec_input += pos_emb
        dec_output = self.dropout(dec_input)
        for layer in self.layers:
            dec_output = layer(dec_output, enc_output, slf_attn_mask, ende_attn_padding_mask)
        dec_output = self.softmax(self.output_layer(dec_output))
        return dec_output
class Transformer(nn.Module):
    def __init__(self, embedding_size, emb_weight, hidden_size, vocab_size):
        super(Transformer, self).__init__()
        self.encoder = Encoder(embedding_size, emb_weight, hidden_size)
        self.decoder = Decoder(embedding_size, emb_weight, hidden_size, vocab_size)
    
    def forward(self, q_seq, ans_seq):
        enc_output = self.encoder(q_seq)
        dec_output = self.decoder(ans_seq, enc_output, q_seq)
        return dec_output

class Chatter:
    def __init__(self):
        embedding_size = 256
        use_cuda = torch.cuda.is_available()
        self.ix2word = pickle.load(open("models/ix2word", "rb"))
        self.word2ix = pickle.load(open("models/word2ix", "rb"))
        weights = pickle.load(open("models/weights", "rb"))
        self.MAXLEN = 20
        self.device = torch.device("cuda" if use_cuda else "cpu")
        vocab_size = len(self.ix2word)
        hidden_size = 256
        self.transformer = Transformer(embedding_size, weights, hidden_size, vocab_size).to(self.device)
        self.transformer.load_state_dict(torch.load("models/transformer.model", map_location=lambda storage, loc: storage))
        self.transformer.eval()
    def response(self, query):
        q_seq = [self.word2ix["<BOS>"]] + [self.word2ix[word] for word in list(query)[:20]] + [self.word2ix["<EOS>"]]
        pad_num = self.MAXLEN + 2 - len(q_seq)
        q_seq += [self.word2ix["<PAD>"]] * pad_num
        q_seq = np.array(q_seq).reshape(self.MAXLEN + 2, 1)
        pos = np.arange(1, self.MAXLEN + 3).reshape(self.MAXLEN + 2, 1)
        q_seq = np.concatenate((q_seq, pos), 1)
        q_seq = torch.LongTensor(q_seq).unsqueeze(0).to(self.device)
        BOS = torch.tensor([[[0,1]]]).to(self.device)
        enc_output = self.transformer.encoder(q_seq)
        for i in range(self.MAXLEN-1):
            if i == 0:
                dec_output = self.transformer.decoder(BOS, enc_output, q_seq)
            else:
                dec_input = torch.cat((BOS[:,:,0], dec_output.max(-1)[-1]), 1).unsqueeze(2)
                dec_pos = torch.arange(1, i+2).long().unsqueeze(0).repeat(1, 1).unsqueeze(2).to(self.device)
                dec_input = torch.cat((dec_input, dec_pos), 2)
                dec_output = self.transformer.decoder(dec_input, enc_output, q_seq)
        pred = dec_output.max(2)[-1]
        last_words = []
        for wix in pred[0]:
            word = self.ix2word[wix.item()]
            last_words.append(word)
            if word == "<EOS>":
                last_words = last_words[:-1]
                break
            if len(set(last_words[-3:])) == 1 and len(last_words) >= 3:
                last_words = last_words[:-2]
                break
        output = "".join(last_words).split("\n")[0]
        if output.startswith("你傳送了"):
            output = "sticker"
        print(output.replace("偶", "我"))