# -*- coding: utf-8 -*-


from flask import Flask, send_from_directory, request, jsonify
import csv
import os
from datetime import datetime
import uuid
import webbrowser
import threading
import socket

app = Flask(__name__, static_folder='.', static_url_path='')

# Create folders
os.makedirs('photos', exist_ok=True)
os.makedirs('videos', exist_ok=True)

# Updated header with amenities and documents columns (pipe-separated strings)
PROPERTY_HEADER = 'id,title,property_type,category,full_address,city,bedrooms,bathrooms,area_sqft,sale_price,per_sqft_price,monthly_rent,seller_name,seller_phone,description,listed_date,photos,videos,amenities,documents'

# Create CSVs if missing (kept amenities.csv & managedocs.csv for legacy)
CSV_FILES = {
    'properties.csv': PROPERTY_HEADER,
    'addons.csv': 'property_type,Apartment,Villa,Townhouse,Penthouse,Office,Shop,Warehouse\ncategory,Sale,Rent',
    'amenities.csv': 'property_id,amenity',
    'managedocs.csv': 'property_id,document'
}

for file, header in CSV_FILES.items():
    if not os.path.exists(file):
        with open(file, 'w', newline='', encoding='utf-8') as f:
            f.write(header + '\n')

# ====================== ROUTES ======================

@app.route('/')
def landing():
    return send_from_directory('.', 'landingpage.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

@app.route('/api/addons')
def get_addons():
    with open('addons.csv', encoding='utf-8') as f:
        lines = f.readlines()
        return jsonify({
            'property_types': lines[0].strip().split(',')[1:],
            'categories': lines[1].strip().split(',')[1:]
        })

@app.route('/api/submit-property', methods=['POST'])
def submit_property():
    try:
        prop_id = str(uuid.uuid4())[:8]

        # Collect photos
        photo_files = []
        for file in request.files.getlist('photos'):
            if file and file.filename:
                ext = file.filename.rsplit('.', 1)[-1].lower()
                filename = f"{prop_id}_{uuid.uuid4().hex[:8]}.{ext}"
                file.save(os.path.join('photos', filename))
                photo_files.append(filename)

        # Collect videos
        video_files = []
        for file in request.files.getlist('videos'):
            if file and file.filename:
                ext = file.filename.rsplit('.', 1)[-1].lower()
                filename = f"{prop_id}_{uuid.uuid4().hex[:8]}.{ext}"
                file.save(os.path.join('videos', filename))
                video_files.append(filename)

        # Amenities/documents as pipe-separated strings
        amenities_list = [item.strip() for item in request.form.getlist('amenities[]') if item.strip()]
        documents_list = [item.strip() for item in request.form.getlist('documents[]') if item.strip()]

        # Property dictionary
        data = {
            'id': prop_id,
            'title': request.form['title'],
            'property_type': request.form['property_type'],
            'category': request.form['category'],
            'full_address': request.form['full_address'],
            'city': request.form['city'],
            'bedrooms': request.form.get('bedrooms', ''),
            'bathrooms': request.form.get('bathrooms', ''),
            'area_sqft': request.form.get('area_sqft', ''),
            'sale_price': request.form.get('sale_price', ''),
            'per_sqft_price': request.form.get('per_sqft_price', ''),
            'monthly_rent': request.form.get('monthly_rent', ''),
            'seller_name': request.form.get('seller_name', ''),
            'seller_phone': request.form.get('seller_phone', ''),
            'description': request.form.get('description', ''),
            'listed_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'photos': '|'.join(photo_files),
            'videos': '|'.join(video_files),
            'amenities': '|'.join(amenities_list),
            'documents': '|'.join(documents_list)
        }

        # Write to CSV
        with open('properties.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data.keys())
            if os.stat('properties.csv').st_size == 0:
                writer.writeheader()
            writer.writerow(data)

        return jsonify({'success': True, 'message': 'Property added successfully!'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ====================== LAN ACCESS FEATURE ======================

def open_browser(port=5000):
    """Opens browser to the LAN IP address instead of 127.0.0.1"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # use Google DNS to detect outbound IP (not an actual connection)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"

    url = f'http://{local_ip}:{port}'
    print(f"\n✨ SERVER RUNNING AT: {url}  (Open this on your PHONE)\n")
    webbrowser.open(url)

# ====================== RUN SERVER ======================

if __name__ == '__main__':
    print("SERENIA REM – Eminent Real Estate (with LAN support enabled)")

    # Open browser on correct local IP
    threading.Thread(target=open_browser, args=(5000,), daemon=True).start()

    # HOST=0.0.0.0 allows access from other devices on same Wi-Fi
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
