from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Product, Sale, SaleItem
from functools import wraps

bp = Blueprint('routes', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('routes.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('routes.admin_dashboard'))
        else:
            return redirect(url_for('routes.cashier_dashboard'))

    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            return jsonify({'success': False, 'message': 'Invalid username or password'})

        login_user(user, remember=True)
        return jsonify({'success': True, 'role': user.role})

    return render_template('login.html', title='Sign In')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.login'))

@bp.route('/')
@login_required
def index():
    if current_user.role == 'admin':
        return redirect(url_for('routes.admin_dashboard'))
    else:
        return redirect(url_for('routes.cashier_dashboard'))

@bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html', title='Admin Dashboard')

@bp.route('/cashier')
@login_required
def cashier_dashboard():
    if current_user.role != 'cashier':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('routes.admin_dashboard'))
    return render_template('cashier/dashboard.html', title='Sales Dashboard')

# API routes will be added below

# API to get all products
@bp.route('/api/products', methods=['GET'])
@login_required
def get_products():
    products = Product.query.all()
    return jsonify([{'id': p.id, 'name': p.name, 'price': p.price, 'stock': p.stock_quantity} for p in products])

# API to add a product (admin only)
@bp.route('/api/products', methods=['POST'])
@login_required
@admin_required
def add_product():
    data = request.get_json()
    new_product = Product(
        name=data['name'],
        price=data['price'],
        stock_quantity=data['stock_quantity']
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Product added successfully.'})

# API to update a product (admin only)
@bp.route('/api/products/<int:product_id>', methods=['PUT'])
@login_required
@admin_required
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    product.name = data.get('name', product.name)
    product.price = data.get('price', product.price)
    product.stock_quantity = data.get('stock_quantity', product.stock_quantity)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Product updated successfully.'})

# API to delete a product (admin only)
@bp.route('/api/products/<int:product_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Product deleted successfully.'})

# API to record a sale (cashier)
@bp.route('/api/sales', methods=['POST'])
@login_required
def record_sale():
    if current_user.role != 'cashier':
        return jsonify({'success': False, 'message': 'Permission denied.'}), 403

    data = request.get_json()
    cart = data.get('cart') # Expected format: [{'id': 1, 'quantity': 2}, ...]
    total_amount = 0

    # Start a transaction
    try:
        # First, calculate total and check stock
        for item in cart:
            product = Product.query.get(item['id'])
            if product is None or product.stock_quantity < item['quantity']:
                return jsonify({'success': False, 'message': f'Not enough stock for {product.name if product else "Unknown item"}.'}), 400
            total_amount += product.price * item['quantity']

        # Create the sale record
        sale = Sale(user_id=current_user.id, total_amount=total_amount)
        db.session.add(sale)

        # Add sale items and update stock
        for item in cart:
            product = Product.query.get(item['id'])
            sale_item = SaleItem(
                sale=sale,
                product_id=product.id,
                quantity=item['quantity'],
                price_at_sale=product.price
            )
            product.stock_quantity -= item['quantity']
            db.session.add(sale_item)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Sale recorded successfully.', 'sale_id': sale.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500

from flask import make_response
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Marco Aesthetics - Receipt', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

@bp.route('/api/receipt/<int:sale_id>')
@login_required
def generate_receipt(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    # Authorization check: only the cashier who made the sale or an admin can view
    if not (current_user.role == 'admin' or current_user.id == sale.user_id):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)

    pdf.cell(0, 10, f"Receipt for Sale ID: {sale.id}", 0, 1)
    pdf.cell(0, 10, f"Date: {sale.timestamp.strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
    pdf.cell(0, 10, f"Cashier: {sale.user.username}", 0, 1)
    pdf.ln(10)

    # Table Header
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(80, 10, 'Product', 1)
    pdf.cell(30, 10, 'Quantity', 1)
    pdf.cell(30, 10, 'Unit Price', 1)
    pdf.cell(30, 10, 'Total', 1)
    pdf.ln()

    # Table Rows
    pdf.set_font('Arial', '', 12)
    for item in sale.items:
        pdf.cell(80, 10, item.product.name, 1)
        pdf.cell(30, 10, str(item.quantity), 1)
        pdf.cell(30, 10, f"K{item.price_at_sale:.2f}", 1)
        pdf.cell(30, 10, f"K{item.quantity * item.price_at_sale:.2f}", 1)
        pdf.ln()

    # Total
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(140, 10, 'Grand Total', 1)
    pdf.cell(30, 10, f"K{sale.total_amount:.2f}", 1)
    pdf.ln(20)

    pdf.cell(0, 10, "Thank you for your purchase!", 0, 1, 'C')

    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=receipt_{sale_id}.pdf'

    return response
