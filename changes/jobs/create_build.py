import sys

from flask import current_app
from sqlalchemy.orm import subqueryload_all

from changes.backends.base import UnrecoverableException
from changes.backends.jenkins.builder import JenkinsBuilder
from changes.config import queue
from changes.constants import Status, Result
from changes.models import Build, BuildPlan, Plan
from changes.utils.locking import lock


@lock
def create_build(build_id):
    build = Build.query.get(build_id)
    if not build:
        return

    build_plan = BuildPlan.query.options(
        subqueryload_all('plan.steps')
    ).filter(
        BuildPlan.build_id == build.id,
    ).join(Plan).first()

    try:
        if not build_plan:
            # TODO(dcramer): once we migrate to build plans we can remove this
            current_app.logger.warning(
                'Got create_build task without build plan: %s', build_id)

            backend = JenkinsBuilder(
                app=current_app,
                base_url=current_app.config['JENKINS_URL'],
            )
            backend.create_build(build)
            # raise Exception('No build plan available for %s' % (build_id,))
        else:
            step = build_plan.plan.steps[0]
            implementation = step.get_implementation()
            implementation.execute(build)

    except UnrecoverableException:
        build.status = Status.finished
        build.result = Result.unknown
        current_app.logger.exception('Unrecoverable exception creating %s', build_id)
        return

    except Exception:
        current_app.logger.exception('Failed to create build %s', build_id)
        raise queue.retry('create_build', kwargs={
            'build_id': build_id,
        }, exc=sys.exc_info())

    queue.delay('sync_build', kwargs={
        'build_id': build_id,
    })
