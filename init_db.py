from app import create_app, db
from app.models import User, Product

def init_database():
    app = create_app()
    with app.app_context():
        # Drop all tables if they exist and create them fresh
        db.drop_all()
        db.create_all()

        # Create users
        admin_user = User(username='admin', role='admin')
        admin_user.set_password('admin123')
        db.session.add(admin_user)

        cashier_user = User(username='cashier', role='cashier')
        cashier_user.set_password('cashier123')
        db.session.add(cashier_user)

        print("Created users: admin, cashier")

        # Create products based on Marco Aesthetics' offerings
        products = [
            {'name': 'Gold Hoop Earrings', 'price': 10.00, 'stock': 50},
            {'name': 'Silver Chain Necklace', 'price': 8.50, 'stock': 40},
            {'name': 'Beaded Bracelet', 'price': 5.00, 'stock': 75},
            {'name': 'Pearl Ring', 'price': 7.00, 'stock': 60},
            {'name': 'Minimalist Barrette', 'price': 3.00, 'stock': 100},
            {'name': 'Layered Necklace', 'price': 9.00, 'stock': 30},
            {'name': 'Simple Studs', 'price': 2.50, 'stock': 120},
            {'name': 'Anklet Chain', 'price': 4.00, 'stock': 80},
            {'name': 'Hair Claw Clip', 'price': 1.00, 'stock': 150},
            {'name': 'Pendant Necklace', 'price': 6.50, 'stock': 55},
        ]

        for p_data in products:
            product = Product(
                name=p_data['name'],
                price=p_data['price'],
                stock_quantity=p_data['stock']
            )
            db.session.add(product)

        print(f"Created {len(products)} sample products.")

        # Commit changes
        db.session.commit()
        print("Database initialized and seeded successfully.")

if __name__ == '__main__':
    init_database()
