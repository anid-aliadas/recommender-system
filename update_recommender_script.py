from app.updating_methods.update_CF_model import update_model
import sys

if(len(sys.argv) < 2): print("bearer token required")

print(update_model( sys.argv[1] ))