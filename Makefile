db-run:
	docker run --rm -v c:\Users\dcabr\Documents\postgresqldb-vol:/var/lib/postgresql/data -e POSTGRES_PASSWORD=mypassword -e POSTGRES_HOST_AUTH_METHOD=trust -p 5432:5432 90da0743e4ed