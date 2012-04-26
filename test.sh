#!/bin/bash
PYTHONPATH=.:$PYTHONPATH django-admin.py test --settings=test_settings mithril
