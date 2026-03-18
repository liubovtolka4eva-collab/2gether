"""
💕 LoveSpace — ГЛАВНЫЙ ФАЙЛ СЕРВЕРА (ПОЛНАЯ ВЕРСИЯ)
Запуск: python app.py
Содержит ВСЕ маршруты: страницы + API
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os, random, string, qrcode, io, base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lovespace-secret-key-2024'
import os
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///lovespace.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ─── МОДЕЛИ БАЗЫ ДАННЫХ ────────────────────────────────────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100))
    avatar = db.Column(db.String(255))
    couple_id = db.Column(db.Integer, db.ForeignKey('couple.id'), nullable=True)
    invite_code = db.Column(db.String(10), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Flask-Login
    is_active = db.Column(db.Boolean, default=True)
    is_authenticated_flag = db.Column(db.Boolean, default=True)
    is_anonymous_flag = db.Column(db.Boolean, default=False)

    def get_id(self): return str(self.id)
    @property
    def is_authenticated(self): return True
    @property
    def is_anonymous(self): return False

    def set_password(self, pw): self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)

    def generate_invite_code(self):
        self.invite_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


class Couple(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    anniversary = db.Column(db.Date, nullable=True)
    members = db.relationship('User', backref='couple', lazy=True)


class CoupleInvite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    to_email = db.Column(db.String(120))
    code = db.Column(db.String(10), unique=True)
    status = db.Column(db.String(20), default='pending')  # pending/accepted/rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey('couple.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    description = db.Column(db.String(255))
    date = db.Column(db.Date, default=date.today)
    type = db.Column(db.String(10))  # income/expense


class SavingsGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey('couple.id'))
    title = db.Column(db.String(100))
    target_amount = db.Column(db.Float)
    current_amount = db.Column(db.Float, default=0)
    emoji = db.Column(db.String(10), default='🎯')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(100))
    day_of_week = db.Column(db.Integer)  # 0=Mon..6=Sun
    start_time = db.Column(db.String(5))  # "HH:MM"
    end_time = db.Column(db.String(5))
    is_busy = db.Column(db.Boolean, default=True)


class HomeTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey('couple.id'))
    title = db.Column(db.String(100))
    points = db.Column(db.Integer, default=10)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    completed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    week_number = db.Column(db.Integer)
    status = db.Column(db.String(20), default='pending')  # pending/done


class MoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.Date, default=date.today)
    mood = db.Column(db.String(20))  # happy/sad/angry/love/neutral/tired
    note = db.Column(db.Text, nullable=True)


class WishlistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(200))
    description = db.Column(db.Text, nullable=True)
    link = db.Column(db.String(500), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    price = db.Column(db.Float, nullable=True)
    priority = db.Column(db.Integer, default=1)
    is_fulfilled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey('couple.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    filename = db.Column(db.String(255))
    caption = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─── LOGIN MANAGER ────────────────────────────────────────────────────────────

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─── МАРШРУТЫ AUTH ───────────────────────────────────────────────────────────

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email уже используется'}), 400
        user = User(
            username=data['username'],
            email=data['email'],
            display_name=data.get('display_name', data['username'])
        )
        user.set_password(data['password'])
        user.generate_invite_code()
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return jsonify({'success': True, 'redirect': '/dashboard'})
    return render_template('auth.html', mode='register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        if user and user.check_password(data['password']):
            login_user(user)
            return jsonify({'success': True, 'redirect': '/dashboard'})
        return jsonify({'error': 'Неверный email или пароль'}), 401
    return render_template('auth.html', mode='login')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    partner = None
    if current_user.couple_id:
        partner = User.query.filter(
            User.couple_id == current_user.couple_id,
            User.id != current_user.id
        ).first()
    return render_template('dashboard.html', user=current_user, partner=partner)


# ─── COUPLE API ──────────────────────────────────────────────────────────────

@app.route('/api/invite/generate', methods=['POST'])
@login_required
def generate_invite():
    if not current_user.invite_code:
        current_user.generate_invite_code()
        db.session.commit()
    # Generate QR
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    invite_url = f"{request.host_url}join/{current_user.invite_code}"
    qr.add_data(invite_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#c9566e", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode()
    return jsonify({
        'code': current_user.invite_code,
        'url': invite_url,
        'qr': qr_b64
    })

@app.route('/join/<code>')
@login_required
def join_couple(code):
    inviter = User.query.filter_by(invite_code=code).first()
    if not inviter or inviter.id == current_user.id:
        return redirect(url_for('dashboard'))
    if current_user.couple_id:
        return redirect(url_for('dashboard'))
    # Create couple
    couple = Couple(name=f"{inviter.display_name} & {current_user.display_name}")
    db.session.add(couple)
    db.session.flush()
    inviter.couple_id = couple.id
    current_user.couple_id = couple.id
    inviter.invite_code = None
    db.session.commit()
    return redirect(url_for('dashboard'))


# ─── WALLET API ──────────────────────────────────────────────────────────────

@app.route('/api/transactions', methods=['GET', 'POST'])
@login_required
def transactions():
    if not current_user.couple_id:
        return jsonify({'error': 'Нет пары'}), 400
    if request.method == 'GET':
        txs = Transaction.query.filter_by(couple_id=current_user.couple_id).order_by(Transaction.date.desc()).all()
        return jsonify([{
            'id': t.id, 'amount': t.amount, 'category': t.category,
            'description': t.description, 'date': str(t.date),
            'type': t.type, 'user_id': t.user_id
        } for t in txs])
    data = request.get_json()
    tx = Transaction(
        couple_id=current_user.couple_id,
        user_id=current_user.id,
        amount=float(data['amount']),
        category=data.get('category', 'Другое'),
        description=data.get('description', ''),
        date=datetime.strptime(data.get('date', str(date.today())), '%Y-%m-%d').date(),
        type=data.get('type', 'expense')
    )
    db.session.add(tx)
    db.session.commit()
    return jsonify({'success': True, 'id': tx.id})

@app.route('/api/savings', methods=['GET', 'POST'])
@login_required
def savings():
    if not current_user.couple_id:
        return jsonify({'error': 'Нет пары'}), 400
    if request.method == 'GET':
        goals = SavingsGoal.query.filter_by(couple_id=current_user.couple_id).all()
        return jsonify([{
            'id': g.id, 'title': g.title, 'target': g.target_amount,
            'current': g.current_amount, 'emoji': g.emoji,
            'percent': round(g.current_amount / g.target_amount * 100) if g.target_amount else 0
        } for g in goals])
    data = request.get_json()
    if data.get('action') == 'add_funds':
        goal = SavingsGoal.query.get(data['id'])
        goal.current_amount = min(goal.current_amount + float(data['amount']), goal.target_amount)
        db.session.commit()
        return jsonify({'success': True})
    goal = SavingsGoal(
        couple_id=current_user.couple_id,
        title=data['title'],
        target_amount=float(data['target']),
        emoji=data.get('emoji', '🎯')
    )
    db.session.add(goal)
    db.session.commit()
    return jsonify({'success': True, 'id': goal.id})


# ─── SCHEDULE API ────────────────────────────────────────────────────────────

@app.route('/api/schedule', methods=['GET', 'POST', 'DELETE'])
@login_required
def schedule():
    if request.method == 'GET':
        user_id = request.args.get('user_id', current_user.id)
        slots = Schedule.query.filter_by(user_id=user_id).all()
        return jsonify([{
            'id': s.id, 'title': s.title, 'day': s.day_of_week,
            'start': s.start_time, 'end': s.end_time
        } for s in slots])
    if request.method == 'DELETE':
        sid = request.get_json().get('id')
        s = Schedule.query.get(sid)
        if s and s.user_id == current_user.id:
            db.session.delete(s)
            db.session.commit()
        return jsonify({'success': True})
    data = request.get_json()
    slot = Schedule(
        user_id=current_user.id,
        title=data['title'],
        day_of_week=int(data['day']),
        start_time=data['start'],
        end_time=data['end'],
        is_busy=True
    )
    db.session.add(slot)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/schedule/free', methods=['GET'])
@login_required
def free_time():
    if not current_user.couple_id:
        return jsonify([])
    partner = User.query.filter(
        User.couple_id == current_user.couple_id,
        User.id != current_user.id
    ).first()
    if not partner:
        return jsonify([])
    my_busy = Schedule.query.filter_by(user_id=current_user.id).all()
    partner_busy = Schedule.query.filter_by(user_id=partner.id).all()
    # Find overlapping free slots (simplified)
    days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    free = []
    for day in range(7):
        my_day = [s for s in my_busy if s.day_of_week == day]
        p_day = [s for s in partner_busy if s.day_of_week == day]
        if not my_day and not p_day:
            free.append({'day': days[day], 'slots': ['10:00-22:00 — весь день свободен!']})
    return jsonify(free)


# ─── HOME TASKS API ──────────────────────────────────────────────────────────

@app.route('/api/tasks', methods=['GET', 'POST'])
@login_required
def home_tasks():
    if not current_user.couple_id:
        return jsonify({'error': 'Нет пары'}), 400
    if request.method == 'GET':
        week = date.today().isocalendar()[1]
        tasks = HomeTask.query.filter_by(couple_id=current_user.couple_id, week_number=week).all()
        users = {u.id: u.display_name for u in User.query.filter_by(couple_id=current_user.couple_id).all()}
        return jsonify([{
            'id': t.id, 'title': t.title, 'points': t.points,
            'status': t.status, 'assigned_to': t.assigned_to,
            'assigned_name': users.get(t.assigned_to, '—'),
            'completed_by': t.completed_by,
            'completed_name': users.get(t.completed_by, '')
        } for t in tasks])
    data = request.get_json()
    if data.get('action') == 'complete':
        task = HomeTask.query.get(data['id'])
        task.status = 'done'
        task.completed_by = current_user.id
        task.completed_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True})
    week = date.today().isocalendar()[1]
    task = HomeTask(
        couple_id=current_user.couple_id,
        title=data['title'],
        points=int(data.get('points', 10)),
        assigned_to=data.get('assigned_to'),
        week_number=week
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/tasks/score', methods=['GET'])
@login_required
def task_scores():
    if not current_user.couple_id:
        return jsonify({})
    week = date.today().isocalendar()[1]
    tasks = HomeTask.query.filter_by(couple_id=current_user.couple_id, week_number=week, status='done').all()
    scores = {}
    for t in tasks:
        scores[t.completed_by] = scores.get(t.completed_by, 0) + t.points
    users = User.query.filter_by(couple_id=current_user.couple_id).all()
    return jsonify([{'user_id': u.id, 'name': u.display_name, 'score': scores.get(u.id, 0)} for u in users])


# ─── MOOD API ────────────────────────────────────────────────────────────────

@app.route('/api/mood', methods=['GET', 'POST'])
@login_required
def mood():
    if request.method == 'GET':
        entries = MoodEntry.query.filter_by(user_id=current_user.id).order_by(MoodEntry.date.desc()).limit(30).all()
        # Also get partner mood if in couple
        partner_entries = []
        if current_user.couple_id:
            partner = User.query.filter(
                User.couple_id == current_user.couple_id,
                User.id != current_user.id
            ).first()
            if partner:
                partner_entries = MoodEntry.query.filter_by(user_id=partner.id).order_by(MoodEntry.date.desc()).limit(30).all()
        return jsonify({
            'mine': [{'date': str(e.date), 'mood': e.mood, 'note': e.note} for e in entries],
            'partner': [{'date': str(e.date), 'mood': e.mood} for e in partner_entries]
        })
    data = request.get_json()
    today = date.today()
    existing = MoodEntry.query.filter_by(user_id=current_user.id, date=today).first()
    if existing:
        existing.mood = data['mood']
        existing.note = data.get('note', '')
    else:
        entry = MoodEntry(user_id=current_user.id, mood=data['mood'], note=data.get('note', ''))
        db.session.add(entry)
    db.session.commit()
    return jsonify({'success': True})


# ─── WISHLIST API ────────────────────────────────────────────────────────────

@app.route('/api/wishlist', methods=['GET', 'POST', 'DELETE'])
@login_required
def wishlist():
    if request.method == 'GET':
        uid = request.args.get('user_id', current_user.id)
        items = WishlistItem.query.filter_by(user_id=uid).order_by(WishlistItem.priority.desc()).all()
        return jsonify([{
            'id': i.id, 'title': i.title, 'description': i.description,
            'link': i.link, 'image_url': i.image_url, 'price': i.price,
            'priority': i.priority, 'is_fulfilled': i.is_fulfilled
        } for i in items])
    if request.method == 'DELETE':
        iid = request.get_json().get('id')
        item = WishlistItem.query.get(iid)
        if item and item.user_id == current_user.id:
            db.session.delete(item)
            db.session.commit()
        return jsonify({'success': True})
    data = request.get_json()
    item = WishlistItem(
        user_id=current_user.id,
        title=data['title'],
        description=data.get('description', ''),
        link=data.get('link', ''),
        image_url=data.get('image_url', ''),
        price=float(data['price']) if data.get('price') else None,
        priority=int(data.get('priority', 1))
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True})


# ─── PHOTOS API ──────────────────────────────────────────────────────────────

@app.route('/api/photos', methods=['GET', 'POST'])
@login_required
def photos():
    if not current_user.couple_id:
        return jsonify({'error': 'Нет пары'}), 400
    if request.method == 'GET':
        ps = Photo.query.filter_by(couple_id=current_user.couple_id).order_by(Photo.created_at.desc()).all()
        users = {u.id: u.display_name for u in User.query.filter_by(couple_id=current_user.couple_id).all()}
        return jsonify([{
            'id': p.id, 'filename': p.filename, 'caption': p.caption,
            'date': p.created_at.strftime('%d.%m.%Y'), 'author': users.get(p.user_id, '?')
        } for p in ps])
    if 'photo' not in request.files:
        return jsonify({'error': 'Нет файла'}), 400
    file = request.files['photo']
    caption = request.form.get('caption', '')
    if file.filename:
        fname = secure_filename(f"{current_user.id}_{datetime.now().timestamp()}_{file.filename}")
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
        photo = Photo(couple_id=current_user.couple_id, user_id=current_user.id, filename=fname, caption=caption)
        db.session.add(photo)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Ошибка загрузки'}), 400

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ─── AI ANALYSIS (через Claude API) ─────────────────────────────────────────

@app.route('/api/ai/analyze', methods=['POST'])
@login_required
def ai_analyze():
    """Анализ расходов через ИИ"""
    if not current_user.couple_id:
        return jsonify({'error': 'Нет пары'}), 400
    txs = Transaction.query.filter_by(couple_id=current_user.couple_id).order_by(Transaction.date.desc()).limit(20).all()
    summary = {}
    for t in txs:
        if t.type == 'expense':
            summary[t.category] = summary.get(t.category, 0) + t.amount
    # Simple rule-based analysis (можно заменить на Claude API)
    tips = []
    total = sum(summary.values())
    for cat, amt in sorted(summary.items(), key=lambda x: -x[1]):
        pct = (amt / total * 100) if total else 0
        if pct > 40:
            tips.append(f"💡 На «{cat}» уходит {pct:.0f}% бюджета — попробуйте сократить эту статью расходов.")
        elif cat.lower() in ['рестораны', 'кафе', 'доставка еды'] and pct > 15:
            tips.append(f"🍳 Много тратите на еду вне дома ({amt:.0f} ₽). Домашняя готовка сэкономит до 50%!")
    if not tips:
        tips.append("✅ Расходы выглядят сбалансированно! Продолжайте в том же духе 💕")
    return jsonify({'tips': tips, 'breakdown': summary})


# ─── ИНИЦИАЛИЗАЦИЯ ───────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ База данных создана")
    app.run(host='0.0.0.0', port=5000, debug=True)


# ══════════════════════════════════════════════════════════════
#  СТРАНИЦЫ — маршруты для всех вкладок (добавлено)
# ══════════════════════════════════════════════════════════════

@app.route('/wallet')
@login_required
def wallet_page():
    return render_template('wallet.html', active='wallet')

@app.route('/schedule')
@login_required
def schedule_page():
    return render_template('schedule.html', active='schedule')

@app.route('/tasks')
@login_required
def tasks_page():
    return render_template('tasks.html', active='tasks')

@app.route('/mood')
@login_required
def mood_page():
    return render_template('mood.html', active='mood')

@app.route('/wishlist')
@login_required
def wishlist_page():
    partner_id = None
    if current_user.couple_id:
        p = User.query.filter(User.couple_id == current_user.couple_id, User.id != current_user.id).first()
        if p:
            partner_id = p.id
    return render_template('wishlist.html', active='wishlist', partner_id=partner_id)

@app.route('/photos')
@login_required
def photos_page():
    return render_template('photos.html', active='photos')

@app.route('/api/me')
@login_required
def api_me():
    return jsonify({
        'id': current_user.id,
        'display_name': current_user.display_name,
        'username': current_user.username,
        'couple_id': current_user.couple_id,
    })
