""" Module to initialise DB

"""

import sqlalchemy
from flask import current_app
from ..models import ActivityType, db


def activity_types(app):
    """Initialize activity types

    Get activity types defined in Flask application configuration (TYPES)
    and load it in the database. This function should be called once at app
    initilisation.
    If DB is not available, it will print a warning in stdout.

    :param app: Application where to extract TYPES
    :type: flask.Application
    :return: None
    """
    try:
        for (aid, atype) in app.config["TYPES"].items():
            activity_type = ActivityType.query.get(aid)
            if activity_type == None:
                activity_type = ActivityType(id=aid)

            activity_type.name = atype["name"]
            activity_type.short = atype["short"]
            activity_type.trigram = atype["trigram"]
            # if order is not specified, default to '50'
            activity_type.order = atype.get("order", 50)
            db.session.add(activity_type)

        # Remove activity not in config
        absent_filter = sqlalchemy.not_(ActivityType.id.in_(app.config["TYPES"].keys()))
        ActivityType.query.filter(absent_filter).delete(synchronize_session=False)
        # due to synchronize_session=False, do not use this session after without
        # commit it

        db.session.commit()

    except sqlalchemy.exc.OperationalError:
        current_app.logger.warning(
            "Cannot configure activity types: db is not available"
        )
    except sqlalchemy.exc.InternalError:
        current_app.logger.warning(
            "Cannot configure activity types: db is not available"
        )
    except sqlalchemy.exc.ProgrammingError:
        current_app.logger.warning(
            "Cannot configure activity types: db is not available"
        )
