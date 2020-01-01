# This file describe all classes we will use in collectives
from ..helpers import current_time

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_utils import PasswordType
from flask_uploads import UploadSet, IMAGES
from wtforms.validators import Email, Length

from datetime import date

from . import db
from .role import RoleIds


# Upload
avatars = UploadSet('avatars', IMAGES)

# Models
class User(db.Model, UserMixin):
    """ Utilisateurs """

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    # E-mail
    mail = db.Column(db.String(100),
                     nullable=False,
                     unique=True,
                     index=True,
                     info={'validators': Email(message="E-mail invalide"),
                           'label': 'Email'})

    # Name
    first_name = db.Column(db.String(100),
                           nullable=False,
                           info={'label': 'Prénom'})
    last_name = db.Column(db.String(100),
                          nullable=False,
                          info={'label': 'Nom'})

    # License number
    license = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
        index=True,
        info={'label': 'Numéro de licence',
              'validators': Length(
                  min=12, max=12,
                  message="Numéro de licence invalide")})

    # Date of birth
    date_of_birth = db.Column(
        db.Date, nullable=False, default=date.today(),
        info={'label': 'Date de naissance'})

    # Hashed password
    password = db.Column(PasswordType(schemes=['pbkdf2_sha512']),
                         nullable=True,
                         info={'label': 'Mot de passe'})

    # Custom avatar
    avatar = db.Column(db.String(100), nullable=True)

    # Contact info
    phone = db.Column(db.String(20), info={'label': 'Téléphone'})
    emergency_contact_name = db.Column(
        db.String(100), nullable=False, default='',
        info={'label': 'Personne à contacter en cas d\'urgence'})
    emergency_contact_phone = db.Column(
        db.String(20), nullable=False, default='',
        info={'label': 'Téléphone en cas d\'urgence'})

    # Internal
    enabled = db.Column(db.Boolean,
                        default=True,
                        info={'label': 'Utilisateur activé'})

    license_expiry_date = db.Column(db.Date)
    last_extranet_sync_time = db.Column(db.DateTime)

    # List of protected field, which cannot be modified by a User
    protected = ['enabled', 'license', 'date_of_birth', 'license_expiry_date',
                 'last_extranet_sync_time']

    # Relationships
    roles = db.relationship('Role', backref='user', lazy=True)
    registrations = db.relationship('Registration', backref='user', lazy=True)

    def save_avatar(self, file):
        if file is not None:
            filename = avatars.save(file, name='user-' + str(self.id) + '.')
            self.avatar = filename

    def check_license_valid_at_time(self, time):
        if self.license_expiry_date is None:
            # Test users licenses never expire
            return True
        return self.license_expiry_date > time.date()

    def matching_roles(self, role_ids):
        return [role for role in self.roles if role.role_id in role_ids]

    def matching_roles_for_activity(self, role_ids, activity_id):
        matching_roles = self.matching_roles(role_ids)
        return [role for role in matching_roles if role.activity_id == activity_id]

    def has_role(self, role_ids):
        return len(self.matching_roles(role_ids)) > 0

    def has_role_for_activity(self, role_ids, activity_id):
        roles = self.matching_roles(role_ids)
        return any([role.activity_id == activity_id for role in roles])

    def is_admin(self):
        return self.has_role([RoleIds.Administrator])

    def is_moderator(self):
        return self.has_role([RoleIds.Moderator,
                              RoleIds.Administrator,
                              RoleIds.President])

    def can_create_events(self):
        return self.has_role([RoleIds.EventLeader,
                              RoleIds.ActivitySupervisor,
                              RoleIds.President,
                              RoleIds.Administrator])

    def can_lead_activity(self, activity_id):
        return self.has_role_for_activity([RoleIds.EventLeader,
                                           RoleIds.ActivitySupervisor],
                                          activity_id)

    def can_read_other_users(self):
        return len(self.roles) > 0

    def supervises_activity(self, activity_id):
        return self.has_role_for_activity([RoleIds.ActivitySupervisor],
                                          activity_id)

    def led_activities(self):
        roles = self.matching_roles([RoleIds.EventLeader,
                                     RoleIds.ActivitySupervisor])
        return set([role.activity_type for role in roles])

    # Format

    def full_name(self):
        return '{} {}'.format(self.first_name, self.last_name.upper())

    def abbrev_name(self):
        return '{} {}'.format(self.first_name, self.last_name[0].upper())

    @property
    def is_active(self):
        return self.enabled and self.check_license_valid_at_time(current_time())
