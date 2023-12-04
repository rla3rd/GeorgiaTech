from flask_login import UserMixin
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from app import db
from app import login

db.Model.metadata.reflect(db.engine)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    __table__ = db.Model.metadata.tables['user'] 

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_is_admin(self, isAdmin):
        self.admin = isAdmin

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Dse(db.Model):
    __table__ = db.Model.metadata.tables['dse']

    def __repr__(self):
        return '<Permno {}>'.format(self.permno)


class Dseall(db.Model):
    __table__ = db.Model.metadata.tables['dseall']    

    def __repr__(self):
        return '<Permno {}>'.format(self.permno)


class Dsedelist(db.Model):
    __table__ = db.Model.metadata.tables['dsedelist'] 

    def __repr__(self):
        return '<Permno {}>'.format(self.permno)   


class Dseexchdates(db.Model):
    __table__ = db.Model.metadata.tables['dseexchdates']  

    def __repr__(self):
        return '<Permno {}>'.format(self.permno)  


class Dsenames(db.Model):
    __table__ = db.Model.metadata.tables['dsenames']    

    def __repr__(self):
        return '<Permno {}>'.format(self.permno)


class Dsenasdin(db.Model):
    __table__ = db.Model.metadata.tables['dsenasdin']    

    def __repr__(self):
        return '<Permno {}>'.format(self.permno)


class Dseshares(db.Model):
    __table__ = db.Model.metadata.tables['dseshares']    

    def __repr__(self):
        return '<Permno {}>'.format(self.permno)


class Dsf(db.Model):
    __table__ = db.Model.metadata.tables['dsf']

    def __repr__(self):
        return '<Permno {}>'.format(self.permno)


class Dsi(db.Model):
    __table__ = db.Model.metadata.tables['dsi']    

    def __repr__(self):
        return '<Date {}>'.format(self.date)


class Dsiy(db.Model):
    __table__ = db.Model.metadata.tables['dsiy']    

    def __repr__(self):
        return '<Date {}>'.format(self.date)


class Stocknames(db.Model):
    __table__ = db.Model.metadata.tables['stocknames']    

    def __repr__(self):
        return '<Permno {}>'.format(self.permno)


class SP500(db.Model):
    __table__ = db.Model.metadata.tables['sp500']

    def __repr__(self):
        return '<Cusip {}>'.format(self.crsp_cusip)


# class Portfolio(db.Model):
#     __table__ = db.Model.metadata.tables['portfolio']
#
#     def __repr__(self):
#         return '<Userid: {}'.format(self.user_id)


class Holdings(db.Model):
    __table__ = db.Model.metadata.tables['holdings']
    def __repr__(self):
        return '<Portid: {}, Permno: {}, Date: {}>'.format([self.port_id, self.permno, self.date])  