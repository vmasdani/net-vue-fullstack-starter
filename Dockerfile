FROM node:18.16.1-alpine3.18 as frontend-env
WORKDIR /App
COPY frontend/. .
RUN --mount=type=cache,target=/root/.yarn YARN_CACHE_FOLDER=/root/.yarn yarn 
RUN --mount=type=cache,target=/root/.yarn YARN_CACHE_FOLDER=/root/.yarn yarn build

FROM mcr.microsoft.com/dotnet/sdk:8.0-jammy AS build-env
WORKDIR /App
COPY ./backend/. ./
RUN --mount=type=cache,id=nuget,target=/root/.nuget/packages dotnet build -c Release -o out
RUN DEBIAN_FRONTEND=noninteractive TZ=Asia/Jakarta apt-get -y install tzdata

FROM mcr.microsoft.com/dotnet/aspnet:8.0-jammy
ENV TZ=Asia/Jakarta
WORKDIR /App
COPY --from=build-env /usr/share/zoneinfo /usr/share/zoneinfo
COPY --from=build-env /App/out .
COPY --from=frontend-env /App/dist/. ./wwwroot
COPY ./backend/.env ./


# Create the directory for file uploads and set permissions
RUN mkdir -p /App/files && \
    chown -R app:app /App/files && \
    chmod 777 /App/files

# ENTRYPOINT ["tail", "-f", "/dev/null"]
ENTRYPOINT ["dotnet", "backend.dll"]