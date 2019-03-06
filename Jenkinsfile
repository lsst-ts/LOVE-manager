pipeline {
  agent any
  environment {
    registryCredential = "dockerhub-inriachile"
    dockerImageName = "inriachile/love-manager:${GIT_BRANCH}"
    dockerImage = ""
  }
  triggers {
    pollSCM("* * * * *")
  }

  stages {
    stage("Build Docker image") {
      when {
        branch "ci-pipeline"
        branch "develop"
      }
      steps {
        script {
          dockerImage = docker.build dockerImageName
        }
      }
    }
    stage("Push Docker image") {
      when {
        branch "ci-pipeline"
        branch "develop"
      }
      steps {
        script {
          docker.withRegistry("", registryCredential) {
            dockerImage.push()
          }
        }
      }
    }
  }
}
