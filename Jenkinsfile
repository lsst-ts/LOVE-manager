pipeline {
  agent any
  environment {
    registryCredential = "dockerhub-inriachile"
    dockerImageName = "lsstts/love-manager:"
    dockerImage = ""
    // SAL setup file
    SAL_SETUP_FILE = "/home/saluser/.setup_dev.sh"
    // LTD credentials
    user_ci = credentials('lsst-io')
    LTD_USERNAME="${user_ci_USR}"
    LTD_PASSWORD="${user_ci_PSW}"
  }

  stages {
    stage("Build Docker image") {
      when {
        anyOf {
          branch "main"
          branch "develop"
          branch "bugfix/*"
          branch "hotfix/*"
          branch "release/*"
          branch "tickets/*"
        }
      }
      steps {
        script {
          def git_branch = "${GIT_BRANCH}"
          def image_tag = git_branch
          def slashPosition = git_branch.indexOf('/')

          if (slashPosition > 0) {
            git_tag = git_branch.substring(slashPosition + 1, git_branch.length())
            git_branch = git_branch.substring(0, slashPosition)
            if (git_branch == "release" || git_branch == "hotfix" || git_branch == "bugfix" || git_branch == "tickets") {
              image_tag = git_tag
            }
          }

          dockerImageName = dockerImageName + image_tag
          echo "dockerImageName: ${dockerImageName}"
          dockerImage = docker.build(dockerImageName, "-f docker/Dockerfile .")
        }
      }
    }
    
    stage("Push Docker image") {
      when {
        anyOf {
          branch "main"
          branch "develop"
          branch "bugfix/*"
          branch "hotfix/*"
          branch "release/*"
          branch "tickets/*"
        }
      }
      steps {
        script {
          docker.withRegistry("", registryCredential) {
            dockerImage.push()
          }
        }
      }
    }

    stage("Test Docker Image") {
      when {
        anyOf {
          branch "main"
          branch "develop"
          branch "bugfix/*"
          branch "hotfix/*"
          branch "release/*"
          branch "tickets/*"
          branch "PR-*"
        }
      }
      steps {
        script {
          sh "docker build -f docker/Dockerfile-test -t love-manager-test ."
          sh "docker run love-manager-test"
        }
      }
    }

    stage("Deploy documentation") {
      agent {
        docker {
          alwaysPull true
          image 'lsstts/develop-env:develop'
          args "--entrypoint=''"
        }
      }
      when {
        branch "main"
        branch "develop"
      }
      steps {
        script {
          sh """
            source ${env.SAL_SETUP_FILE}
            # Create docs
            cd ./docsrc
            pip install -r requirements.txt
            sh ./create_docs.sh
            cd ..
            # Upload docs
            pip install ltd-conveyor
            ltd upload --product love-manager --git-ref ${GIT_BRANCH} --dir ./docs
          """
        }
      }
    }

    stage("Trigger develop deployment") {
      when {
        branch "develop"
      }
      steps {
        build(job: '../LOVE-integration-tools/develop', wait: false)
      }
    }
    stage("Trigger main deployment") {
      when {
        branch "main"
      }
      steps {
        build(job: '../LOVE-integration-tools/main', wait: false)
      }
    }
  }
}
