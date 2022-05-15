from app import app, db
import os


if __name__ == '__main__':
	db.create_all()
	app.run(debug=(os.environ.get('DEBUG_VALUE') == 'True'))
