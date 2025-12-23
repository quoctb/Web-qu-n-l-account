from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
from sqlalchemy import func

# Cấu hình font cho tiếng Việt
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game_accounts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Helper function để format số tiền theo đơn vị ngàn
def format_thousands(value):
    """Chuyển đổi số tiền sang đơn vị ngàn (K)"""
    if value is None:
        return "0"
    try:
        value = float(value)
        if value >= 1000:
            # Chia cho 1000 và làm tròn 1 chữ số thập phân
            result = value / 1000
            if result == int(result):
                return f"{int(result):,} K"
            else:
                return f"{result:,.1f} K"
        else:
            # Nếu nhỏ hơn 1000, hiển thị số gốc
            return f"{value:,.0f}"
    except (ValueError, TypeError):
        return "0"

# Đăng ký filter cho Jinja2
app.jinja_env.filters['thousands'] = format_thousands

# Models
class GameAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_name = db.Column(db.String(100), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='available')  # available, sold, reserved
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sold_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<GameAccount {self.account_name}>'

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('game_account.id'), nullable=False)
    buyer_name = db.Column(db.String(100))
    sale_price = db.Column(db.Float, nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    account = db.relationship('GameAccount', backref=db.backref('sales', lazy=True))
    
    def __repr__(self):
        return f'<Sale {self.id}>'

# Routes
@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    # Thống kê tổng quan
    total_accounts = GameAccount.query.count()
    available_accounts = GameAccount.query.filter_by(status='available').count()
    sold_accounts = GameAccount.query.filter_by(status='sold').count()
    total_revenue = db.session.query(func.sum(Sale.sale_price)).scalar() or 0
    
    # Tạo biểu đồ doanh thu theo ngày
    revenue_chart = create_revenue_chart()
    
    # Tạo biểu đồ số lượng account theo game
    game_chart = create_game_distribution_chart()
    
    # Tạo biểu đồ doanh thu theo game
    revenue_by_game_chart = create_revenue_by_game_chart()
    
    return render_template('dashboard.html',
                         total_accounts=total_accounts,
                         available_accounts=available_accounts,
                         sold_accounts=sold_accounts,
                         total_revenue=total_revenue,
                         revenue_chart=revenue_chart,
                         game_chart=game_chart,
                         revenue_by_game_chart=revenue_by_game_chart)

@app.route('/accounts')
def accounts():
    status_filter = request.args.get('status', 'all')
    game_filter = request.args.get('game', 'all')
    
    query = GameAccount.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if game_filter != 'all':
        query = query.filter_by(game_name=game_filter)
    
    accounts = query.order_by(GameAccount.id.asc()).all()
    games_query = db.session.query(GameAccount.game_name).distinct().all()
    games = [g[0] for g in games_query] if games_query else []
    
    return render_template('accounts.html', accounts=accounts, games=games, 
                         status_filter=status_filter, game_filter=game_filter)

@app.route('/account/add', methods=['GET', 'POST'])
def add_account():
    if request.method == 'POST':
        try:
            # Nhân giá với 1000 vì người dùng nhập theo đơn vị ngàn
            price_input = float(request.form['price'])
            price = price_input * 1000
            
            account = GameAccount(
                game_name=request.form['game_name'],
                account_name=request.form['account_name'],
                level=int(request.form['level']),
                price=price,
                status=request.form['status'],
                description=request.form.get('description', '')
            )
            db.session.add(account)
            db.session.commit()
            flash('Đã thêm account thành công!', 'success')
            return redirect(url_for('accounts'))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi thêm account: {str(e)}', 'danger')
    
    games_query = db.session.query(GameAccount.game_name).distinct().all()
    games = [g[0] for g in games_query] if games_query else []
    return render_template('add_account.html', games=games)

@app.route('/account/<int:id>/edit', methods=['GET', 'POST'])
def edit_account(id):
    account = GameAccount.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Nhân giá với 1000 vì người dùng nhập theo đơn vị ngàn
            price_input = float(request.form['price'])
            price = price_input * 1000
            
            account.game_name = request.form['game_name']
            account.account_name = request.form['account_name']
            account.level = int(request.form['level'])
            account.price = price
            account.status = request.form['status']
            account.description = request.form.get('description', '')
            db.session.commit()
            flash('Đã cập nhật account thành công!', 'success')
            return redirect(url_for('accounts'))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi cập nhật account: {str(e)}', 'danger')
    
    games_query = db.session.query(GameAccount.game_name).distinct().all()
    games = [g[0] for g in games_query] if games_query else []
    # Chia giá cho 1000 để hiển thị trong form (người dùng nhập theo đơn vị ngàn)
    account_price_display = (account.price / 1000) if account.price else 0
    return render_template('edit_account.html', account=account, games=games, account_price_display=account_price_display)

@app.route('/account/<int:id>/delete', methods=['POST'])
def delete_account(id):
    try:
        account = GameAccount.query.get_or_404(id)
        db.session.delete(account)
        db.session.commit()
        flash('Đã xóa account thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi xóa account: {str(e)}', 'danger')
    return redirect(url_for('accounts'))

@app.route('/account/<int:id>/sell', methods=['GET', 'POST'])
def sell_account(id):
    account = GameAccount.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Nhân giá bán với 1000 vì người dùng nhập theo đơn vị ngàn
            sale_price_input = float(request.form['sale_price'])
            sale_price = sale_price_input * 1000
            
            sale = Sale(
                account_id=account.id,
                buyer_name=request.form.get('buyer_name', ''),
                sale_price=sale_price
            )
            account.status = 'sold'
            account.sold_at = datetime.utcnow()
            db.session.add(sale)
            db.session.commit()
            flash('Đã bán account thành công!', 'success')
            return redirect(url_for('accounts'))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi bán account: {str(e)}', 'danger')
    
    # Chia giá cho 1000 để hiển thị trong form (người dùng nhập theo đơn vị ngàn)
    account_price_display = (account.price / 1000) if account.price else 0
    return render_template('sell_account.html', account=account, account_price_display=account_price_display)

@app.route('/sales')
def sales():
    sales = Sale.query.order_by(Sale.sale_date.desc()).all()
    return render_template('sales.html', sales=sales)

# Helper functions for charts
def create_revenue_chart():
    try:
        # Lấy doanh thu 30 ngày gần nhất
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        sales = Sale.query.filter(Sale.sale_date >= start_date).all()
        
        # Nhóm theo ngày
        daily_revenue = {}
        for sale in sales:
            date_key = sale.sale_date.date()
            daily_revenue[date_key] = daily_revenue.get(date_key, 0) + sale.sale_price
        
        dates = sorted(daily_revenue.keys())
        revenues = [daily_revenue[date] for date in dates]
        
        # Xử lý trường hợp không có dữ liệu
        if not dates:
            plt.figure(figsize=(10, 6))
            plt.text(0.5, 0.5, 'Chua co du lieu ban hang', 
                    ha='center', va='center', fontsize=14)
            plt.title('Doanh Thu Theo Ngay (30 Ngay Gan Nhat)', fontsize=14, fontweight='bold')
            plt.axis('off')
        else:
            plt.figure(figsize=(10, 6))
            plt.plot(dates, revenues, marker='o', linewidth=2, markersize=8)
            plt.title('Doanh Thu Theo Ngay (30 Ngay Gan Nhat)', fontsize=14, fontweight='bold')
            plt.xlabel('Ngay', fontsize=12)
            plt.ylabel('Doanh Thu (VND)', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        return plot_url
    except Exception as e:
        plt.close()
        # Trả về biểu đồ trống nếu có lỗi
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, f'Loi: {str(e)}', ha='center', va='center', fontsize=12)
        plt.axis('off')
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        return plot_url

def create_game_distribution_chart():
    try:
        # Đếm số lượng account theo game
        game_counts = db.session.query(
            GameAccount.game_name,
            func.count(GameAccount.id)
        ).group_by(GameAccount.game_name).all()
        
        games = [g[0] for g in game_counts]
        counts = [g[1] for g in game_counts]
        
        # Xử lý trường hợp không có dữ liệu
        if not games:
            plt.figure(figsize=(10, 6))
            plt.text(0.5, 0.5, 'Chua co account nao', 
                    ha='center', va='center', fontsize=14)
            plt.title('So Luong Account Theo Game', fontsize=14, fontweight='bold')
            plt.axis('off')
        else:
            plt.figure(figsize=(10, 6))
            plt.bar(games, counts, color='steelblue', alpha=0.7)
            plt.title('So Luong Account Theo Game', fontsize=14, fontweight='bold')
            plt.xlabel('Game', fontsize=12)
            plt.ylabel('So Luong', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        return plot_url
    except Exception as e:
        plt.close()
        # Trả về biểu đồ trống nếu có lỗi
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, f'Loi: {str(e)}', ha='center', va='center', fontsize=12)
        plt.axis('off')
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        return plot_url

def create_revenue_by_game_chart():
    try:
        # Tính doanh thu theo game
        revenue_by_game = db.session.query(
            GameAccount.game_name,
            func.sum(Sale.sale_price)
        ).join(Sale).group_by(GameAccount.game_name).all()
        
        if not revenue_by_game:
            return None
        
        games = [g[0] for g in revenue_by_game]
        revenues = [g[1] for g in revenue_by_game]
        
        plt.figure(figsize=(10, 6))
        plt.barh(games, revenues, color='green', alpha=0.7)
        plt.title('Doanh Thu Theo Game', fontsize=14, fontweight='bold')
        plt.xlabel('Doanh Thu (VND)', fontsize=12)
        plt.ylabel('Game', fontsize=12)
        plt.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        return plot_url
    except Exception as e:
        plt.close()
        return None

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)

