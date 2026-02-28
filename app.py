from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, bcrypt, User, Article, Message
from datetime import date
import re

app = Flask(__name__)

# ── CONFIG ──
app.config['SECRET_KEY'] = 'storynest-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///storynest.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ── INIT EXTENSIONS ──
db.init_app(app)
bcrypt.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'error'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ── SAMPLE DATA ──
SAMPLE_ARTICLES = [
    {
        'title': 'The Art of Mindful Writing',
        'category': 'Writing Tips',
        'date': '2024-03-15',
        'status': 'published',
        'content': '<p>Mindful writing is a practice that combines the art of storytelling with the principles of mindfulness. When we write mindfully, we bring our full attention to the present moment, noticing the thoughts and feelings that arise as we craft each sentence.</p><p>Discover how to harness the power of mindfulness to elevate your creative writing. By slowing down and paying attention to each word, writers can unlock deeper layers of meaning and connection in their work.</p><p>Start by setting aside dedicated time for your writing, free from distractions. Take a few deep breaths before you begin, and notice how you feel in your body and mind.</p>'
    },
    {
        'title': 'Building Stories That Resonate',
        'category': 'Storytelling',
        'date': '2024-03-10',
        'status': 'published',
        'content': '<p>Great storytelling is about creating an emotional connection with your reader. The most memorable stories are those that tap into universal human experiences — love, loss, hope, and transformation.</p><p>Learn the essential elements of storytelling that connect with readers on a deeper level. Character development, narrative arc, and authentic dialogue are the building blocks of a resonant story.</p><p>When writers draw from their own experiences and observations, their stories carry a weight and authenticity that readers can feel.</p>'
    },
    {
        'title': 'The Digital Age of Literature',
        'category': 'Culture',
        'date': '2024-03-05',
        'status': 'published',
        'content': '<p>Technology has fundamentally changed how we create, consume, and share stories. From e-readers to podcasts, from social media microfiction to long-form digital journalism, literature is evolving at an unprecedented pace.</p><p>Exploring how technology is reshaping the way we write, read, and share stories in the modern era. Digital platforms have democratized publishing, giving voice to writers who might never have found traditional publishing routes.</p><p>Yet amid this abundance, the challenge is discoverability and depth.</p>'
    },
    {
        'title': "Finding Your Author's Voice",
        'category': 'Personal Growth',
        'date': '2024-02-28',
        'status': 'published',
        'content': '<p>Your voice as a writer is the most distinctive tool in your craft. It is the sum of your experiences, your reading, your observations, and your unique way of seeing the world.</p><p>A journey into discovering your unique voice as a writer and how to stay authentic in your craft. Many writers spend years trying to sound like their favorite authors, only to discover that their most powerful work comes when they stop imitating.</p><p>Voice develops through practice, through reading widely, and through the courage to write the things only you can write.</p>'
    },
    {
        'title': 'The Joy of Handwritten Notes',
        'category': 'Creativity',
        'date': '2024-02-22',
        'status': 'published',
        'content': '<p>In a world of digital devices, there is something profoundly satisfying about putting pen to paper. Handwriting engages the brain differently than typing — it slows us down and deepens our engagement with the material.</p><p>Why putting pen to paper can unlock creativity and connection in ways that digital tools simply cannot replicate. Studies have shown that taking notes by hand improves comprehension and retention.</p><p>For writers, keeping a handwritten journal can be a powerful creative practice.</p>'
    },
    {
        'title': 'Publishing in the Modern Era',
        'category': 'Publishing',
        'date': '2024-02-15',
        'status': 'published',
        'content': '<p>The publishing landscape has transformed dramatically over the past decade. Traditional publishing, self-publishing, and hybrid models now coexist, offering writers more paths to readers than ever before.</p><p>Navigate the landscape of self-publishing, traditional publishing, and hybrid models to find the right path for your work. Each route comes with its own trade-offs.</p><p>The key is to align your publishing strategy with your goals as a writer.</p>'
    },
]

def seed_database():
    """Create admin user and sample articles if database is empty."""
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@storynest.com')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('✅ Admin user created.')

    if Article.query.count() == 0:
        admin = User.query.filter_by(username='admin').first()
        for data in SAMPLE_ARTICLES:
            article = Article(
                title    = data['title'],
                category = data['category'],
                date     = data['date'],
                status   = data['status'],
                content  = data['content'],
                user_id  = admin.id
            )
            db.session.add(article)
        db.session.commit()
        print('✅ Sample articles created.')


# ── HELPER ──
def strip_html(content):
    return re.sub(r'<[^>]+>', '', content)


# ════════════════════════════════
# PUBLIC ROUTES
# ════════════════════════════════

@app.route('/')
def home():
    articles = Article.query.filter_by(status='published')\
                            .order_by(Article.date.desc()).all()
    return render_template('home.html', articles=articles)


@app.route('/article/<int:article_id>')
def article(article_id):
    article = Article.query.get_or_404(article_id)
    return render_template('article.html', article=article)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    success = False
    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        email   = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if name and email and message:
            msg = Message(
                name    = name,
                email   = email,
                subject = subject,
                message = message
            )
            db.session.add(msg)
            db.session.commit()
            success = True
        else:
            flash('Please fill in all required fields.', 'error')

    return render_template('contact.html', success=success)


@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    results = []
    if query:
        results = Article.query.filter(
            Article.status == 'published',
            db.or_(
                Article.title.ilike(f'%{query}%'),
                Article.category.ilike(f'%{query}%'),
                Article.content.ilike(f'%{query}%')
            )
        ).order_by(Article.date.desc()).all()
    return render_template('search.html', results=results, query=query)


# ════════════════════════════════
# AUTH ROUTES
# ════════════════════════════════

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    error = None
    if request.method == 'POST':
        username         = request.form.get('username', '').strip()
        email            = request.form.get('email', '').strip()
        password         = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # ── VALIDATIONS ──
        if not username or not email or not password:
            error = 'Please fill in all fields.'

        elif len(username) < 3:
            error = 'Username must be at least 3 characters.'

        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'

        elif password != confirm_password:
            error = 'Passwords do not match.'

        elif User.query.filter_by(username=username).first():
            error = 'Username already taken. Please choose another.'

        elif User.query.filter_by(email=email).first():
            error = 'Email already registered. Please sign in.'

        else:
            # ── CREATE USER ──
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            # Auto login after register
            login_user(new_user)
            flash(f'Welcome to StoryNest, {username}! Start writing your first story.', 'success')
            return redirect(url_for('dashboard'))

    return render_template('register.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user     = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid username or password.'

    return render_template('login.html', error=error)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


# ════════════════════════════════
# DASHBOARD ROUTES
# ════════════════════════════════

@app.route('/dashboard')
@login_required
def dashboard():
    articles  = Article.query.filter_by(user_id=current_user.id)\
                             .order_by(Article.date.desc()).all()
    total     = len(articles)
    published = len([a for a in articles if a.status == 'published'])
    drafts    = len([a for a in articles if a.status == 'draft'])
    return render_template('dashboard.html',
                           articles=articles,
                           total=total,
                           published=published,
                           drafts=drafts)


@app.route('/admin/add', methods=['GET', 'POST'])
@login_required
def add_article():
    if request.method == 'POST':
        title    = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        date_val = request.form.get('date', '').strip()
        content  = request.form.get('content', '').strip()
        status   = request.form.get('status', 'published')

        if title and content and date_val:
            paragraphs = content.split('\n\n')
            formatted  = ''.join(
                f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()
            )
            article = Article(
                title    = title,
                category = category or 'Uncategorized',
                date     = date_val,
                content  = formatted,
                status   = status,
                user_id  = current_user.id
            )
            db.session.add(article)
            db.session.commit()

            if status == 'published':
                flash('Article published successfully!', 'success')
            else:
                flash('Article saved as draft.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Please fill in all required fields.', 'error')

    today = date.today().isoformat()
    return render_template('add_article.html', today=today)


@app.route('/admin/edit/<int:article_id>', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    article = Article.query.get_or_404(article_id)

    if article.user_id != current_user.id:
        flash('You do not have permission to edit this article.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title    = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        date_val = request.form.get('date', '').strip()
        content  = request.form.get('content', '').strip()
        status   = request.form.get('status', 'published')

        if title and content and date_val:
            paragraphs = content.split('\n\n')
            formatted  = ''.join(
                f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()
            )
            article.title    = title
            article.category = category or 'Uncategorized'
            article.date     = date_val
            article.content  = formatted
            article.status   = status

            db.session.commit()
            flash('Article updated successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Please fill in all required fields.', 'error')

    article.content = strip_html(article.content)
    return render_template('edit_article.html', article=article)


@app.route('/admin/delete/<int:article_id>', methods=['POST'])
@login_required
def delete_article(article_id):
    article = Article.query.get_or_404(article_id)

    if article.user_id != current_user.id:
        flash('You do not have permission to delete this article.', 'error')
        return redirect(url_for('dashboard'))

    db.session.delete(article)
    db.session.commit()
    flash('Article deleted.', 'success')
    return redirect(url_for('dashboard'))


# ── RUN ──
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database()
    app.run(debug=True)