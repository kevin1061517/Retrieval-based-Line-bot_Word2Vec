from sklearn import feature_extraction
from sklearn.feature_extraction.text import CountVectorizer 
from sklearn.feature_extraction.text import TfidfTransformer
import jieba as jb
import pickle
from gensim.models import word2vec
from scipy import spatial

class CandReplyer:
	def __init__(self):
		# self.vectorizer = pickle.load(open("models/vectorizer", "rb"))
		# self.transformer = pickle.load(open("models/tfidf", "rb"))
		# self.wmodel = word2vec.Word2Vec.load("models/wmodel.w2v")
		self.thres = 0.4
		self.candidate_replies = {
		    "招呼": "Hi 我是kevin",
		    "預設": "抱歉我不懂您的意思"
		}

	def sent2vec(self, sent):
		sent_split = jb.lcut(sent)
		sent_blank = " ".join(sent_split)
		sent_tfidf = self.transformer.transform(self.vectorizer.transform([sent_blank])).toarray()[0]
		sent_vec = []
		for word in sent_split:
			if word in self.wmodel.wv.vocab:
				if word in self.vectorizer.vocabulary_:
					weight = sent_tfidf[self.vectorizer.vocabulary_[word]]
				else:
					weight = 0.05
				if len(sent_vec) == 0:
					sent_vec = weight * self.wmodel.wv[word]
				else:
					sent_vec += weight * self.wmodel.wv[word]
		return sent_vec / len(sent_split)

	def reply(self, query):
		query_vec = self.sent2vec(query)
		max_similarity = -1
		cur_cand = "預設"
		for cand in self.candidate_replies.keys():
			# print(cand, ": ", end="")
			cand_vec = self.sent2vec(cand)
			simi = 1 - spatial.distance.cosine(query_vec, cand_vec)
			# print(simi)
			if simi > max_similarity and simi > self.thres:
				max_similarity = simi
				cur_cand = cand
		return self.candidate_replies[cur_cand]
