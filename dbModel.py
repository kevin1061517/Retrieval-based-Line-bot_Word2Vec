
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://cecabqbzzhnmvn:ebf5dc46ca1e2337c2b6c1c0471318e7e7fe3a7329339e8d9b205bd1fd73027c@ec2-107-20-185-27.compute-1.amazonaws.com:5432/de4f2jdtp52vub'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)


class usermessage(db.Model):
    __tablename__ = 'usermessage'

    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50))
    message = db.Column(db.Text)
    birth_date = db.Column(db.TIMESTAMP)

    def __init__(self
                 , id
                 , user_id
                 , message
                 , birth_date
                 ):
        self.id = id
        self.user_id = user_id
        self.message = message
        self.birth_date = birth_date


if __name__ == '__main__':
    manager.run()