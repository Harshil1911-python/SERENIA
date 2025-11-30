from flask import Flask, request, jsonify
import csv
import os
from datetime import datetime
import uuid

app = Flask(__name__)

# Create folders (only for this one request – temporary on Vercel)
os.makedirs('photos', exist_ok=True)
os.makedirs('videos', exist_ok=True)

# Your existing properties.csv header
PROPERTY_HEADER = 'id,title,property_type,category,full_address,city,bedrooms,bathrooms,area_sqft,sale_price,per_sqft_price,monthly_rent,seller_name,seller_phone,description,listed_date,photos,videos,amenities,documents'

@app.route('/api/addons')
def get_addons():
    return jsonify({
        'property_types': ['Apartment','Villa','Townhouse','Penthouse','Office','Shop','Warehouse'],
        'categories': ['Sale','Rent']
    })

@app.route('/api/submit-property', methods=['POST'])
def submit_property():
    try:
        prop_id = str(uuid.uuid4())[:8]

        photo_files = []
        for file in request.files.getlist('photos'):
            if file and file.filename:
                filename = f"{prop_id}_{uuid.uuid4().hex[:8]}.{file.filename.rsplit('.',1)[1]}"
                file.save(os.path.join('photos', filename))
                photo_files.append(filename)

        video_files = []
        for file in request.files.getlist('videos'):
            if file and file.filename:
                filename = f"{prop_id}_{uuid.uuid4().hex[:8]}.{file.filename.rsplit('.',1)[1]}"
                file.save(os.path.join('videos', filename))
                video_files.append(filename)

        amenities = '|'.join([v for v in request.form.getlist('amenities[]') if v])
        documents = '|'.join([v for v in request.form.getlist('documents[]') if v])

        new_property = [
            prop_id,
            request.form['title'],
            request.form['property_type'],
            request.form['category'],
            request.form['full_address'],
            request.form['city'],
            request.form.get('bedrooms',''),
            request.form.get('bathrooms',''),
            request.form.get('area_sqft',''),
            request.form.get('sale_price',''),
            request.form.get('per_sqft_price',''),
            request.form.get('monthly_rent',''),
            request.form.get('seller_name',''),
            request.form.get('seller_phone',''),
            request.form.get('description',''),
            datetime.now().strftime('%d/%m/%Y %H:%M'),
            '|'.join(photo_files),
            '|'.join(video_files),
            amenities,
            documents
        ]

        with open('properties.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if os.stat('properties.csv').st_size == 0:
                writer.writerow(PROPERTY_HEADER.split(','))
            writer.writerow(new_property)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500