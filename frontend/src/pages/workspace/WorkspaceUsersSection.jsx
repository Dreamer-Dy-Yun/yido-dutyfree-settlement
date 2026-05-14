function WorkspaceUsersSection({
  loading,
  users,
  onCreateUser,
  onEditUser,
  onToggleUserActivation,
  onDeleteUser,
  onResetPassword,
}) {
  return (
    <div className="workspace-users-section">
      <div className="workspace-section-header">
        <h2>유저 목록</h2>
        <button onClick={onCreateUser} className="workspace-create-button">
          유저 추가
        </button>
      </div>

      {loading ? (
        <div className="workspace-loading">로딩 중...</div>
      ) : (
        <table className="workspace-users-table">
          <thead>
            <tr>
              <th>이름</th>
              <th>이메일</th>
              <th>역할</th>
              <th>부서</th>
              <th>연락처</th>
              <th>상태</th>
              <th>작업</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.name}</td>
                <td>{user.e_mail}</td>
                <td>{user.role === 'admin' ? '관리자' : '유저'}</td>
                <td>{user.department || '-'}</td>
                <td>{user.contact || '-'}</td>
                <td>
                  <span className={`workspace-status ${user.is_active ? 'active' : 'inactive'}`}>
                    {user.is_active ? '활성' : '비활성'}
                  </span>
                </td>
                <td>
                  <div className="workspace-user-action-buttons">
                    <button onClick={() => onEditUser(user)} className="workspace-edit-button">
                      수정
                    </button>
                    <button
                      onClick={() => onToggleUserActivation(user)}
                      className={`workspace-activation-button ${user.is_active ? 'deactivate' : 'activate'}`}
                    >
                      {user.is_active ? '비활성화' : '활성화'}
                    </button>
                    <button onClick={() => onDeleteUser(user)} className="workspace-delete-button">
                      삭제
                    </button>
                    <button
                      onClick={() => onResetPassword(user.id)}
                      className="workspace-reset-button"
                    >
                      비밀번호 재설정
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default WorkspaceUsersSection;
