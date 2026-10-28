ARG cycle=develop
ARG py_version=3.13

FROM ts-dockerhub.lsst.org/conda_package_builder:latest AS builder

ARG py_version

WORKDIR /tmp/build
COPY . .

RUN source /home/saluser/.setup.sh && \
    CONDA_BLD_PATH=/tmp/conda-bld conda build --python ${py_version} -c lsstts/label/main --prefix-length 100 --no-test conda/

FROM ts-dockerhub.lsst.org/deploy-env:${cycle}

ARG project_path=python/love/manager

LABEL maintainer Sebastian Aranda <sebastian.aranda@noirlab.edu>

COPY --chown=saluser:saluser --from=builder /tmp/conda-bld /tmp/conda-bld

RUN source /home/saluser/.setup_sal_env.sh && \
	conda index /tmp/conda-bld && \
    conda install -c file:///tmp/conda-bld love-manager -y && \
    conda clean -afy && \
    rm -rf /tmp/conda-bld

# Copy fixtures for UI framework and API
COPY --chown=saluser:saluser ${project_path}/ui_framework/fixtures /home/saluser/ui_framework/fixtures
COPY --chown=saluser:saluser ${project_path}/api/fixtures /home/saluser/api/fixtures

# Create static and media directories
#RUN mkdir -p /home/saluser/love-manager/static /home/saluser/love-manager/media

# Copy source code and build project
RUN source /home/saluser/.setup_sal_env.sh && \
    manage_love collectstatic --noinput

# Expose static and media files and port
VOLUME /home/saluser/love-manager
EXPOSE 8000

# Set env variables for runtime (to be replaced in docker-compose files)
ENV ADMIN_USER_PASS=test
ENV USER_USER_PASS=test
ENV CMD_USER_PASS=test
# ENV NO_DEBUG=True

# Run uvicorn server in runtime
COPY --chown=saluser:saluser docker/runserver-prod.sh /home/saluser/.startup.sh
RUN chmod a+x /home/saluser/.startup.sh
