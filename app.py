from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from export_pdf import generate_pdf_data
import os

app = Flask(__name__)

# Konfigurasi database SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Model Database
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_barang = db.Column(db.String(100), nullable=False)
    kategori = db.Column(db.String(100), nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)
    lokasi = db.Column(db.String(100), nullable=False)


# Home / Daftar Barang
@app.route('/')
def index():

    search = request.args.get('search', '')

    if search:
        items = Item.query.filter(
            Item.nama_barang.contains(search)
        ).all()
    else:
        items = Item.query.all()

    total_barang = len(items)

    kategori = db.session.query(
        Item.kategori
    ).distinct().count()

    lokasi = db.session.query(
        Item.lokasi
    ).distinct().count()

    return render_template(
        'index.html',
        items=items,
        total_barang=total_barang,
        kategori=kategori,
        lokasi=lokasi
    )


# Tambah Barang
@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        item = Item(
            nama_barang=request.form['nama_barang'],
            kategori=request.form['kategori'],
            jumlah=request.form['jumlah'],
            lokasi=request.form['lokasi']
        )

        db.session.add(item)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('add.html')


# Edit Barang
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_item(id):
    item = Item.query.get_or_404(id)

    if request.method == 'POST':
        item.nama_barang = request.form['nama_barang']
        item.kategori = request.form['kategori']
        item.jumlah = request.form['jumlah']
        item.lokasi = request.form['lokasi']

        db.session.commit()

        return redirect(url_for('index'))

    return render_template('edit.html', item=item)


# Hapus Barang
@app.route('/delete/<int:id>')
def delete_item(id):
    item = Item.query.get_or_404(id)

    db.session.delete(item)
    db.session.commit()

    return redirect(url_for('index'))


# Preview Export PDF
@app.route('/preview')
def preview():
    data = generate_pdf_data()
    return render_template('preview.html', data=data)


# Download PDF
@app.route('/download-pdf')
def download_pdf():
    pdf_path = generate_pdf_data(generate_pdf=True)

    return send_file(
        pdf_path,
        as_attachment=True
    )


# Initialize database tables on app startup
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)