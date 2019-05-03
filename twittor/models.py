from twittor import db, login_manager
from datetime import datetime
from hashlib import md5
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(120), default="No information yet!")
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    tweets = db.relationship('Tweet', backref='author',lazy='dynamic')
    shoppingCart = db.relationship('ShoppingCart',backref='owner',lazy = 'dynamic')

    cards = db.relationship('Card', backref='owner')
    orders = db.relationship('Order',backref='owner')

    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return 'id={}, username={}, email={}, password_hash={}'.format(
            self.id,self.username,self.email,self.password_hash
        )

    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash, password)
    def avatar(self, size=80):
        md5_digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            md5_digest, size
        )
    def follow(self,user):
        if not self.is_following(user):
            self.followed.append(user)
    def unfollow(self,user):
        if self.is_following(user):
            self.followed.remove(user)
    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() >0
    def own_and_followed_tweets(self):
        followed = Tweet.query.join(
            followers, (followers.c.followed_id == Tweet.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Tweet.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Tweet.create_time.desc())
       
        
class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return 'id={}, tweet={}, create at={}, user_id={}'.format(
            self.id,self.body,self.create_time,self.user_id
        )

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class Card(db.Model):
    UserId = db.Column(db.Integer, db.ForeignKey('user.id'))
    CardNumber = db.Column(db.String(16),primary_key=True)
    ExpirDate = db.Column(db.String(5),nullable=False)
    CardType = db.Column(db.String(6),nullable=False)
    Company = db.Column(db.String(10),nullable=False)

    def __init__(self,UserId,CardNumber,ExpirDate,CardType,Company):
        self.UserId = UserId;
        self.CardType = CardType;
        self.ExpirDate = ExpirDate;
        self.CardNumber = CardNumber;
        self.Company = Company;
        
    def __repr__(self):
       return 'UserId={}, CardNumber={}, ExpirDate={}, CardType={},Company={}'.format(
           self.UserId,self.CardNumber,self.ExpirDate,self.CardType,self.Company
       )

class Seller(db.Model):
    SellerId = db.Column(db.Integer, primary_key=True)
    SellerName = db.Column(db.String(64),nullable=False)
    Address = db.Column(db.String(64),nullable=False)
    PhoneNumber = db.Column(db.String(64),unique=True,nullable=False)
    Rating = db.Column(db.Float)

    Inventory = db.relationship('Inventory',backref='user')
    

    def __repr__(self):
       return 'UserId={}, CardNumber={}, ExpirDate={}, CardType={},Company={}'.format(
           self.UserId,self.CardNumber,self.ExpirDate,self.CardType,self.Company
       )

class Product(db.Model):
    SellerId = db.Column(db.Integer,db.ForeignKey('seller.SellerId'),primary_key=True)
    ProductId = db.Column(db.Integer,unique=True,primary_key=True)
    ProductName = db.Column(db.String(64),nullable=False)
    Descriptions = db.Column(db.String(256),nullable=False)
    Price = db.Column(db.Float)
    Category  = db.Column(db.String(256),nullable=False)
    Rating  = db.Column(db.Float,default=0)
    
    
    def __repr__(self):
       return 'SellerId={}, ProductId={}, ProductName={}, Descriptions={}, Price={}, Category={}, Rating={}'.format(
           self.SellerId,self.ProductId,self.ProductName,self.Descriptions,self.Price,self.Category,self.Rating
       )
   
class Inventory(db.Model):
    SellerId = db.Column(db.Integer,db.ForeignKey('seller.SellerId'),primary_key=True)
    #ProductId = db.Column(db.Integer,db.ForeignKey('product.ProductId'),primary_key=True)
    ProductId = db.relationship('Product',backref='inventory',lazy=True)
    Stock = db.Column(db.Integer)
    
    def __repr__(self):
       return 'SellerId={}, ProductId={}, Stock={}'.format(
           self.SellerId,self.ProductId,self.Stock
       )

class ShoppingCart(db.Model):
    # Don't need cardId. A user has an unique cart.
    UserId = db.Column(db.Integer,db.ForeignKey('user.id'))
    ProductId = db.Column(db.Integer,db.ForeignKey('product.ProductId'),primary_key=True)
    Quantity = db.Column(db.Integer,nullable=False)
    Price  = db.Column(db.Double,default=0,nullable=False)
    
    
    def __repr__(self):
       return 'ProductId={}, Quantity={}, UserId={}, Price={}'.format(
           self.ProductId,self.Quantity,self.UserId,self.Price
       )
    def calculatePrice(self,quantity):
       product = Product.query.filter_by(ProductId = self.ProductId)
       return product.Price * quantity

    def changeQuantity(self,quantity):
       self.Quantity = quantity;
       self.Price = calculatePrice(self,quantity)
       return self

    def quantityInc(self):
       changeQuantity(self,self.Quantity+1)
       return self

    def quantityDec(self):
        changeQuantity(self,self.Quantity-1)
        return self

class Order(db.Model):
    UserId = db.Column(db.Integer,db.ForeignKey('user.id'),primary_key=True)
    ProductId = db.relationship('Product',backref='order',lazy=True)
    OrderNumber = db.Column(db.Integer,primary_key=True)
    Quantity = db.Column(db.Integer)
    #Discount = db.Column(db.Integer,default=0)
    #status: 'U'=Unpaid,'P'=Paid,'D'=Delivered,'C'=Cancelled,'R'=Return
    Status = db.Column(db.String(1),nullable=False,default='U')
    
    
    def __repr__(self):
       return 'ProductId={},Quantity={}, OrderNumber={}, Status={}'.format(
           self.ProductId,self.Quantity,self.OrderNumber,self.Status
       )