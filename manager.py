from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from app import create_app
from exts import db

from apps.front import models

SampleModel = models.SampleModel


app = create_app()

manager = Manager(app)
Migrate(app, db)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()