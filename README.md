# DrugDevTT

create database
```bash
python new_db.py
```
**run api**
```bash
python app.py
```
**run unittest**
```bash
python -m unittest test_app.py
```
**run celery worker**
```bash
celery worker -A app.celery -B --loglevel=info
```
**run celery monitor**
```bash
celery -A app.celery flower
```

Api URLs

**Contact**
```text
List all contacts   	        GET 	http://[hostname]/contact						
Find a contact by username      GET 	http://[hostname]/contact/[contact_username]	
Create a new contact 	        POST 	http://[hostname]/contact						
Update a contacts               PUT 	http://[hostname]/contact/[contact_username]	
Delete a contact 	        DELETE 	http://[hostname]/contact/[contact_username]
```
**Email**
```text
Send mail 	            POST 	http://[hostname]/contact/[contact_username]/email
Get user emails 	    GET 	http://[hostname]/contact/[contact_username]/email
Get user email by id  	    GET 	http://[hostname]/contact/[contact_username]/email/[email_id]
Delete user email by id     DELETE 	http://[hostname]/contact/[contact_username]/email/[email_id]
```
