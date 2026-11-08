import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
import Layout from "./components/Layout";
import { Spinner } from "./components/ui";
import Welcome from "./pages/Welcome";
import GamePage from "./pages/student/GamePage";
import Games from "./pages/student/Games";
import LearnPath from "./pages/student/LearnPath";
import LessonPage from "./pages/student/LessonPage";
import MyClass from "./pages/student/MyClass";
import QuizPage from "./pages/student/QuizPage";
import ReviewPage from "./pages/student/ReviewPage";
import StudentHome from "./pages/student/StudentHome";
import Tutor from "./pages/student/Tutor";
import ClassPage from "./pages/teacher/ClassPage";
import Library from "./pages/teacher/Library";
import QuizEditor from "./pages/teacher/QuizEditor";
import LessonEditor from "./pages/teacher/LessonEditor";
import StudentReport from "./pages/teacher/StudentReport";
import TeacherHome from "./pages/teacher/TeacherHome";

export default function App() {
  const { user, loading } = useAuth();
  if (loading) return <div className="grid min-h-screen place-items-center"><Spinner label="Loading SmartKids…" /></div>;
  if (!user) return <Routes><Route path="*" element={<Welcome />} /></Routes>;

  return (
    <Routes>
      <Route element={<Layout />}>
        {user.role === "Student" ? (
          <>
            <Route index element={<StudentHome />} />
            <Route path="learn" element={<LearnPath />} />
            <Route path="lesson/:id" element={<LessonPage />} />
            <Route path="quiz/:id" element={<QuizPage />} />
            <Route path="review/:id" element={<ReviewPage />} />
            <Route path="games" element={<Games />} />
            <Route path="games/:slug" element={<GamePage />} />
            <Route path="tutor" element={<Tutor />} />
            <Route path="class" element={<MyClass />} />
          </>
        ) : (
          <>
            <Route index element={<TeacherHome />} />
            <Route path="classes/:id" element={<ClassPage />} />
            <Route path="students/:id" element={<StudentReport />} />
            <Route path="library" element={<Library />} />
            <Route path="quizzes/:id/edit" element={<QuizEditor />} />
            <Route path="lessons/:id/edit" element={<LessonEditor />} />
            <Route path="lesson/:id" element={<LessonPage />} />
            <Route path="review/:id" element={<ReviewPage />} />
          </>
        )}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
