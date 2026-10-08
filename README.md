<h1 align="center">Meditrack: Hospital Management System</h1>

<p align="center"><b>Role-based hospital workflow from reception to pharmacy: patients, appointments, consultations, lab tests and prescriptions.</b></p>

<p align="center">![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white) ![Django](https://img.shields.io/badge/Django-092E20?logo=django&logoColor=white) ![Django REST](https://img.shields.io/badge/Django%20REST-A30000?logo=django&logoColor=white) ![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)</p>

## Overview

Django hospital management system with role-based portals for receptionists, doctors, lab technicians, pharmacists and admins: patients, appointments, lab tests, prescriptions and medication schedules.

## Features

- Custom user model with five roles: Admin, Receptionist, Doctor, Lab Technician, Pharmacist, each with its own dashboard
- Reception: register patients and book appointments
- Doctors: consultations, lab test requests, prescribing after results
- Lab: test queue, result entry, patient history
- Pharmacy: dispense prescriptions and build medication schedules
- Admin: staff management and profiles
- REST serializers for API access

## Tech stack

Python · Django · Django REST · SQLite

## Getting started

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install django djangorestframework
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver      # http://127.0.0.1:8000
```

## Project structure

`backend/` project settings · `hospital/` models, forms, views and per-role templates (`templates/doctor`, `templates/pharmacist`, ...)

---

<p align="center">Built by <a href="https://github.com/allan818181"><b>Allan Muganyizi Deus</b></a> · Full-Stack &amp; DevOps Engineer · Dar es Salaam, Tanzania<br/>
<a href="https://www.linkedin.com/in/allan-deus-4b888631a">LinkedIn</a> · <a href="mailto:allandeus014@gmail.com">Email</a></p>
