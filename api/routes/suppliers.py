from flask import Blueprint, request, jsonify  
from models import Supplier  # Assuming there's a Supplier model defined in models.py

supplier_bp = Blueprint('supplier', __name__)  

# Create a new supplier  
@supplier_bp.route('/suppliers', methods=['POST'])  
def create_supplier():  
    data = request.get_json()  
    new_supplier = Supplier(**data)  
    new_supplier.save()  
    return jsonify(new_supplier.to_dict()), 201

# Get all suppliers  
@supplier_bp.route('/suppliers', methods=['GET'])  
def get_suppliers():  
    suppliers = Supplier.query.all()  
    return jsonify([supplier.to_dict() for supplier in suppliers]), 200

# Get a supplier by ID  
@supplier_bp.route('/suppliers/<int:id>', methods=['GET'])  
def get_supplier(id):  
    supplier = Supplier.query.get(id)  
    if supplier is None:  
        return jsonify({'message': 'Supplier not found'}), 404  
    return jsonify(supplier.to_dict()), 200

# Update a supplier  
@supplier_bp.route('/suppliers/<int:id>', methods=['PUT'])  
def update_supplier(id):  
    data = request.get_json()  
    supplier = Supplier.query.get(id)  
    if supplier is None:  
        return jsonify({'message': 'Supplier not found'}), 404  
    for key, value in data.items():  
        setattr(supplier, key, value)  
    supplier.save()  
    return jsonify(supplier.to_dict()), 200

# Delete a supplier  
@supplier_bp.route('/suppliers/<int:id>', methods=['DELETE'])  
def delete_supplier(id):  
    supplier = Supplier.query.get(id)  
    if supplier is None:  
        return jsonify({'message': 'Supplier not found'}), 404  
    supplier.delete()  
    return jsonify({'message': 'Supplier deleted successfully'}), 204