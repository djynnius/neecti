from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return {'message': 'Welcome to co.nnecti.ng'}

@main_bp.route('/health')
def health():
    return {'status': 'healthy'}
