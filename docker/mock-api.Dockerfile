FROM golemfactory/golem-client-mock:0.1.2 

COPY mock-api/nlog.config /app/nlog.config
COPY mock-api/appsettings.json /app/appsettings.json
