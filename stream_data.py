#!/usr/bin/env python

import random
import time

from datetime import datetime

from changes import mock
from changes.config import db, create_app
from changes.constants import Result, Status
from changes.db.utils import get_or_create
from changes.events import publish_build_update, publish_job_update
from changes.models import (
    Change, Job, JobStep, LogSource, TestResultManager, ProjectPlan
)

app = create_app()
app_context = app.app_context()
app_context.push()


def create_new_change(project, **kwargs):
    return mock.change(project=project, **kwargs)


def create_new_entry(project):
    new_change = (random.randint(0, 2) == 1)
    if not new_change:
        try:
            change = Change.query.all()[0]
        except IndexError:
            new_change = True

    if new_change:
        author = mock.author()
        revision = mock.revision(project.repository, author)
        change = create_new_change(
            project=project,
            author=author,
            message=revision.message,
        )
    else:
        change.date_modified = datetime.utcnow()
        db.session.add(change)
        revision = mock.revision(project.repository, change.author)

    if random.randint(0, 1) == 1:
        patch = mock.patch(project)
    else:
        patch = None
    source = mock.source(
        project.repository, revision_sha=revision.sha, patch=patch)

    date_started = datetime.utcnow()

    build = mock.build(
        author=change.author,
        project=project,
        source=source,
        message=change.message,
        result=Result.unknown,
        status=Status.in_progress,
        date_started=date_started,
    )
    db.session.commit()
    publish_build_update(build)

    for x in xrange(0, random.randint(1, 3)):
        job = mock.job(
            build=build,
            change=change,
            status=Status.in_progress,
        )
        db.session.commit()
        publish_job_update(job)

        for step in JobStep.query.filter(JobStep.job == job):
            logsource = LogSource(
                job=job,
                project=job.project,
                step=step,
                name=step.label,
            )
            db.session.add(logsource)
            db.session.commit()

            offset = 0
            for x in xrange(30):
                lc = mock.logchunk(source=logsource, offset=offset)
                db.session.commit()
                offset += lc.size

    return build


def update_existing_entry(project):
    try:
        job = Job.query.filter(
            Job.status == Status.in_progress,
        )[0]
    except IndexError:
        return create_new_entry(project)

    job.status = Status.finished
    job.result = Result.failed if random.randint(0, 3) == 1 else Result.passed
    job.date_finished = datetime.utcnow()
    db.session.add(job)
    publish_job_update(job)

    test_results = []
    for _ in xrange(50):
        if job.result == Result.failed:
            result = Result.failed if random.randint(0, 3) == 1 else Result.passed
        else:
            result = Result.passed
        test_results.append(mock.test_result(job, result=result))
    TestResultManager(job).save(test_results)

    if job.status == Status.finished:
        job.build.status = job.status
        job.build.result = job.result
        job.build.date_finished = job.date_finished
        db.session.add(job.build)
        publish_build_update(job.build)

    return job


def gen(project):
    if random.randint(0, 5) == 1:
        build = create_new_entry(project)
    else:
        build = update_existing_entry(project)

    db.session.commit()

    return build


def loop():
    repository = mock.repository()
    project = mock.project(repository)
    plan = mock.plan()
    get_or_create(ProjectPlan, where={
        'plan': plan,
        'project': project,
    })

    while True:
        build = gen(project)
        print 'Pushed build {0} on {1}'.format(build.id, project.slug)
        time.sleep(1)


if __name__ == '__main__':
    loop()
