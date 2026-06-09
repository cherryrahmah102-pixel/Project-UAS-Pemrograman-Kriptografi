import json
import hashlib
import qrcode
from datetime import datetime
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image
)
from reportlab.lib import colors
from reportlab.lib import pagesizes
from reportlab.lib.styles import getSampleStyleSheet

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

import os


def generate_keys():
    if not os.path.exists("private_key.pem"):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        public_key = private_key.public_key()

        with open("private_key.pem", "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
            )

        with open("public_key.pem", "wb") as f:
            f.write(
                public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
            )


def generate_pdf_data(generate_pdf=False):
    from app import app, Item

    with app.app_context():

        generate_keys()

        items = Item.query.order_by(Item.id).all()

        books_data = []

        for item in items:
            books_data.append({
                "id": item.id,
                "nama_barang": item.nama_barang,
                "kategori": item.kategori,
                "jumlah": item.jumlah,
                "lokasi": item.lokasi
            })

        json_data = json.dumps(
            books_data,
            sort_keys=True
        )

        sha256_hash = hashlib.sha256(
            json_data.encode()
        ).hexdigest()

        with open("private_key.pem", "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )

        signature = private_key.sign(
            sha256_hash.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        signature_hex = signature.hex()

        qr_path = "static/qr/hash_qr.png"

        qr = qrcode.make(sha256_hash)
        qr.save(qr_path)

        timestamp = datetime.now().strftime(
            "%d-%m-%Y %H:%M:%S"
        )

        if generate_pdf:
            pdf_path = "static/generated_pdf/inventory_report.pdf"

            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=pagesizes.A4
            )

            styles = getSampleStyleSheet()
            elements = []

            title = Paragraph(
                "Laporan Data Inventaris Barang",
                styles['Title']
            )

            elements.append(title)
            elements.append(Spacer(1, 10))

            table_data = [
                ["ID", "Nama Barang", "Kategori", "Jumlah", "Lokasi"]
            ]

            for item in books_data:
                table_data.append([
                    item["id"],
                    item["nama_barang"],
                    item["kategori"],
                    item["jumlah"],
                    item["lokasi"]
                ])

            table = Table(table_data)

            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.pink),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            elements.append(table)
            elements.append(Spacer(1, 10))

            elements.append(
                Paragraph(
                    f"<b>SHA-256 Hash:</b> {sha256_hash}",
                    styles['BodyText']
                )
            )

            elements.append(
                Paragraph(
                    f"<b>Digital Signature:</b> {signature_hex[:100]}...",
                    styles['BodyText']
                )
            )

            elements.append(
                Paragraph(
                    f"<b>Timestamp:</b> {timestamp}",
                    styles['BodyText']
                )
            )

            elements.append(Spacer(1, 10))
            elements.append(
                Image(qr_path, width=120, height=120)
            )

            doc.build(elements)

            return pdf_path

        return {
            "items": books_data,
            "hash": sha256_hash,
            "signature": signature_hex,
            "timestamp": timestamp,
            "qr_path": qr_path
        }