pipeline {
  agent any

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Setup Python') {
      steps {
        bat '''
        py -m venv venv
        call venv\\Scripts\\activate
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        '''
      }
    }

    stage('test_bi_mat_cleopatra_flow') {
      steps { bat 'call venv\\Scripts\\activate && pytest -v -s tests\\test_bi_mat_cleopatra_flow.py' }
    }
    stage('test_cung_hy_phat_tai_flow') {
      steps { bat 'call venv\\Scripts\\activate && pytest -v -s tests\\test_cung_hy_phat_tai_flow.py' }
    }
    stage('test_hac_thoai_ngo_khong_flow') {
      steps { bat 'call venv\\Scripts\\activate && pytest -v -s tests\\test_hac_thoai_ngo_khong_flow.py' }
    }
    stage('test_kho_bau_tu_linh_flow') {
      steps { bat 'call venv\\Scripts\\activate && pytest -v -s tests\\test_kho_bau_tu_linh_flow.py' }
    }
    stage('test_linh_chau_at_ty_flow') {
      steps { bat 'call venv\\Scripts\\activate && pytest -v -s tests\\test_linh_chau_at_ty_flow.py' }
    }
    stage('test_mini_poker_flow') {
      steps { bat 'call venv\\Scripts\\activate && pytest -v -s tests\\test_mini_poker_flow.py' }
    }
    stage('test_sac_xuan_cho_tet_flow') {
      steps { bat 'call venv\\Scripts\\activate && pytest -v -s tests\\test_sac_xuan_cho_tet_flow.py' }
    }
    stage('test_son_tinh_thuy_tinh_flow') {
      steps { bat 'call venv\\Scripts\\activate && pytest -v -s tests\\test_son_tinh_thuy_tinh_flow.py' }
    }
    stage('test_taixiu_mini_flow') {
      steps { bat 'call venv\\Scripts\\activate && pytest -v -s tests\\test_taixiu_mini_flow.py' }
    }
    stage('test_tren_duoi_mini_flow') {
      steps { bat 'call venv\\Scripts\\activate && pytest -v -s tests\\test_tren_duoi_mini_flow.py' }
    }
    stage('test_txmd5_mini_flow') {
      steps { bat 'call venv\\Scripts\\activate && pytest -v -s tests\\test_txmd5_mini_flow.py' }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'reports/**/*,logs/**/*', allowEmptyArchive: true
    }
  }
}
