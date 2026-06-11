import os, shutil, tempfile, traceback
from datetime import datetime
from flask import jsonify, request, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
from models.models import (
    Company, db, User, Role, RolePermission, Permission, Branch,
    Warehouse, ProductCategory, Unit, Product, Customer,
    Inventory, InventoryLedger, ProductionBatch,
    SalesQuotation, SalesQuotationItem, SalesOrder, SalesOrderItem,
    Invoice, Payment, GoodsReceiveVoucher, GRVItem,
    GoodsIssueVoucher, GIVItem, Transfer, TransferItem,
    LoadingAuthorization, StockAdjustment, StockAdjustmentItem,
    ReturnVoucher, ReturnVoucherItem, AuditLog,
)
from utils.error_handlers import NotFoundError, ValidationError, AppError
from api.decorators import role_required, audit_log
from . import company_bp


@company_bp.route('', methods=['GET'])
@jwt_required()
def get_company():
    company = Company.query.first()
    if not company:
        return jsonify({'company': None}), 200
    return jsonify({'company': company.to_dict()}), 200


@company_bp.route('', methods=['PUT'])
@jwt_required()
@audit_log('update', 'Company')
@role_required('Owner')
def update_company():
    company = Company.query.first()
    if not company:
        raise NotFoundError('Company not found. Seed the database first.')

    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    if data.get('name') is not None:
        company.name = data['name'].strip()
    if data.get('legal_name') is not None:
        company.legal_name = data['legal_name'].strip()
    if data.get('tax_id') is not None:
        company.tax_id = data['tax_id'].strip()
    if data.get('logo_url') is not None:
        company.logo_url = data['logo_url'].strip()
    if data.get('address') is not None:
        company.address = data['address'].strip()
    if data.get('phone') is not None:
        company.phone = data['phone'].strip()
    if data.get('email') is not None:
        company.email = data['email'].strip()
    if data.get('website') is not None:
        company.website = data['website'].strip()
    if data.get('currency') is not None:
        company.currency = data['currency'].strip()
    if data.get('fiscal_year_start') is not None:
        company.fiscal_year_start = data['fiscal_year_start'].strip()
    if data.get('is_active') is not None:
        company.is_active = bool(data['is_active'])

    company.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'company': company.to_dict(), 'message': 'Company updated successfully'}), 200


@company_bp.route('/backup', methods=['GET'])
@jwt_required()
@role_required('Owner')
def backup_database():
    db_path = _get_db_path()
    if not db_path or not os.path.exists(db_path):
        raise NotFoundError('Database file not found')
    backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'eta_backup_{timestamp}.db')
    # Ensure no lingering connections
    db.session.close()
    shutil.copy2(db_path, backup_path)
    return send_file(backup_path, as_attachment=True, download_name=f'selam_terranite_backup_{timestamp}.db')


@company_bp.route('/backup', methods=['POST'])
@jwt_required()
@role_required('Owner')
def restore_database():
    db_path = _get_db_path()
    if not db_path:
        raise NotFoundError('Database configuration not found')
    if 'file' not in request.files:
        raise ValidationError('No file uploaded')
    f = request.files['file']
    if f.filename == '' or not f.filename.endswith('.db'):
        raise ValidationError('Upload a valid .db file')
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        f.save(tmp.name)
        tmp_path = tmp.name
    try:
        # Validate the uploaded file is a valid SQLite DB
        import sqlite3
        conn = sqlite3.connect(tmp_path)
        conn.execute('SELECT 1')
        conn.close()
        backup_path = db_path + '.restore_bak'
        db.session.close()
        # Remove old backup if it exists
        if os.path.exists(backup_path):
            os.remove(backup_path)
        # Rename current DB to backup, put new DB in place
        os.rename(db_path, backup_path)
        shutil.copy2(tmp_path, db_path)
        os.remove(tmp_path)
        return jsonify({'message': 'Database restored successfully. Restart recommended.'}), 200
    except Exception as e:
        current_app.logger.error('Database restore failed: %s', traceback.format_exc())
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        if os.path.exists(backup_path):
            try:
                os.replace(backup_path, db_path)
            except Exception:
                pass
        if isinstance(e, (ValidationError, NotFoundError)):
            raise
        raise AppError(f'Database restore failed: {str(e)}', status_code=500)


@company_bp.route('/reset', methods=['POST'])
@jwt_required()
@audit_log('reset', 'Database')
@role_required('Owner')
def reset_database():
    data = request.get_json() or {}

    preserve = {
        'users': data.get('keep_users', True),
        'branches': data.get('keep_branches', True),
        'company': data.get('keep_company', True),
        'products': data.get('keep_products', False),
        'customers': data.get('keep_customers', False),
    }

    models_to_delete = []

    if not preserve['users']:
        models_to_delete.extend([AuditLog, ReturnVoucherItem, ReturnVoucher,
            StockAdjustmentItem, StockAdjustment, LoadingAuthorization,
            GIVItem, GoodsIssueVoucher, GRVItem, GoodsReceiveVoucher,
            Payment, Invoice, SalesOrderItem, SalesOrder,
            SalesQuotationItem, SalesQuotation, TransferItem, Transfer,
            InventoryLedger, Inventory, ProductionBatch, Customer,
            Product, Unit, ProductCategory, Warehouse, Branch,
            RolePermission, Permission, User, Role])

    if not preserve['branches']:
        models_to_delete.extend([ReturnVoucherItem, ReturnVoucher,
            StockAdjustmentItem, StockAdjustment, LoadingAuthorization,
            GIVItem, GoodsIssueVoucher, GRVItem, GoodsReceiveVoucher,
            Payment, Invoice, SalesOrderItem, SalesOrder,
            SalesQuotationItem, SalesQuotation, TransferItem, Transfer,
            InventoryLedger, Inventory, ProductionBatch, Customer,
            Warehouse, Branch])

    if not preserve['products']:
        models_to_delete.extend([ReturnVoucherItem, ReturnVoucher,
            StockAdjustmentItem, StockAdjustment, LoadingAuthorization,
            GIVItem, GoodsIssueVoucher, GRVItem, GoodsReceiveVoucher,
            Payment, Invoice, SalesOrderItem, SalesOrder,
            SalesQuotationItem, SalesQuotation, TransferItem, Transfer,
            InventoryLedger, Inventory, ProductionBatch,
            Product, Unit, ProductCategory])

    if not preserve['customers']:
        models_to_delete.extend([ReturnVoucherItem, ReturnVoucher,
            StockAdjustmentItem, StockAdjustment, LoadingAuthorization,
            GIVItem, GoodsIssueVoucher, Payment, Invoice,
            SalesOrderItem, SalesOrder, SalesQuotationItem, SalesQuotation,
            Customer])

    if not preserve['company']:
        models_to_delete.append(Company)

    if not models_to_delete:
        return jsonify({'message': 'Nothing to reset — all data preserved.'}), 200

    seen = set()
    unique_models = []
    for m in models_to_delete:
        if m not in seen:
            seen.add(m)
            unique_models.append(m)

    try:
        for model in unique_models:
            model.query.delete()
        db.session.commit()
        msg = 'Database reset completed.'
        kept = [k for k, v in preserve.items() if v]
        if kept:
            msg += f' Preserved: {', '.join(kept)}.'
        return jsonify({'message': msg}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Database reset failed: %s', traceback.format_exc())
        if isinstance(e, (ValidationError, NotFoundError)):
            raise
        raise AppError(f'Reset failed: {str(e)}', status_code=500)


def _get_db_path():
    uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    if uri.startswith('sqlite:///'):
        rel_path = uri[len('sqlite:///'):]
        instance_path = current_app.instance_path
        return os.path.join(instance_path, rel_path)
    return None
