# file: /db.py

from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


engine = create_engine('sqlite:///skyshopAPI.db', echo=True)
Base = declarative_base()


class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    api_name = Column(String)
    order_id = Column(String)
    email_user = Column(String)
    status = Column(String)
    order_details = Column(Text)
    
    def __repr__(self):
        return f"<Order {self.api_name} {self.order_id}"

class JollyOrder(Base):
    __tablename__ = 'jm_orders'
    
    id = Column(Integer, primary_key=True)
    api_name = Column(String)
    order_id = Column(String)
    message_id = Column(String)
    email_user = Column(String)
    status = Column(String)
    order_details = Column(Text)
    
    def __repr__(self):
        return f"<Order {self.api_name} {self.order_id} {self.message_id}"


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


class DatabaseManager:
    def add_order(self, api_name, order_id, email_user, status, order_details):
        order = Order(api_name=api_name, order_id=order_id, email_user=email_user, status=status, order_details=order_details)
        session.add(order)
        session.commit()
        
    def get_all_orders(self):
        return session.query(Order).all()
    
    def get_orders_by_status(self, status):
        return session.query(Order).filter(Order.status == status).all()
    
    def get_order_by_id(self, order_id):
        return session.query(Order).get(order_id)
    
    def update_order(self, order_id, status, new_order_details):
        order = session.query(Order).filter(Order.order_id == order_id).first()
        order.status = status
        order.order_details = new_order_details
        session.commit()
        
    def delete_order(self, order_id):
        order = session.query(Order).filter(Order.order_id == order_id).first()
        session.delete(order)
        session.commit()
        
    def add_jm_order(self, api_name, order_id, message_id, email_user, status, order_details):
        order = JollyOrder(api_name=api_name, order_id=order_id, message_id=message_id, email_user=email_user, status=status, order_details=order_details)
        session.add(order)
        session.commit()
        
    def get_all_jm_orders(self):
        return session.query(JollyOrder).all()
    
    def get_orders_jm_by_status(self, status):
        return session.query(JollyOrder).filter(JollyOrder.status == status).all()
    
    def get_order_jm_by_id(self, order_id, message_id):
        return session.query(JollyOrder).filter(JollyOrder.order_id == order_id, JollyOrder.message_id == message_id).first()
    
    def update_jm_order(self, order_id, message_id, new_status, new_order_details):
        order = session.query(JollyOrder).filter(JollyOrder.order_id == order_id, JollyOrder.message_id == message_id).first()
        order.status = new_status
        order.order_details = new_order_details
        session.commit()
    
    def delete_jm_order(self, order_id, message_id):
        order = session.query(JollyOrder).filter(JollyOrder.order_id == order_id, JollyOrder.message_id == message_id).first()
        session.delete(order)
        session.commit()