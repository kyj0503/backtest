const disabledError = () => new Error('커뮤니티 기능은 현재 비활성화되어 있습니다.');

export async function listPosts() {
  return Promise.resolve({ items: [] });
}

export async function createPost(_title: string, _content: string) {
  return Promise.reject(disabledError());
}

export async function getPost(_postId: number) {
  return Promise.reject(disabledError());
}

export async function addComment(_postId: number, _content: string) {
  return Promise.reject(disabledError());
}
