import axios from 'axios';
import { BookInfo } from './components/book-info';
import { UserInfo } from './components/user-info';

function App() {
  return (
    <>
      <ResouceLoader resouceUrl={'/users/1'} resourceName={'user'}>
        <UserInfo />
      </ResouceLoader>

      <ResouceLoader resouceUrl={'/books/1'} resourceName={'book'}>
        <BookInfo />
      </ResouceLoader>
    </>
  );
}

export default App;
