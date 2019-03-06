pipeline {
  agent any

  stages {
    stage('Build') {
      when {
        branch 'ci-pipeline'
      }
      steps {
        echo 'Building..'
      }
    }
  }
}
