from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
import sqlite3
from geopy.geocoders import Nominatim

store_home_relation_bp = Blueprint('store_home_relation', __name__, url_prefix='/store_home_relation')

@store_home_relation_bp.route('/store_home_relation', methods=['GET', 'POST'])
def store_home():


    return render_template('stores/store_registration.html')

