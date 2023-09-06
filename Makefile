lint:
	docker run -it --rm --env-file=.lint -v $(CURDIR):/app divio/lint /bin/lint ${ARGS}

