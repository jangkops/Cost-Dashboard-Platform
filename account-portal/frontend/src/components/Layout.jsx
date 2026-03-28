import Sidebar from "./Sidebar";
import { Outlet, useNavigate } from "react-router-dom";
import { ArrowRightOnRectangleIcon } from "@heroicons/react/24/outline";

export default function Layout({ onLogout }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    onLogout();
    navigate("/login");
  };

  return (
    <div className="flex min-h-screen bg-sky-50">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <div className="bg-white shadow-sm h-14 flex items-center justify-end px-6">
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
          >
            <ArrowRightOnRectangleIcon className="w-5 h-5" />
            로그아웃
          </button>
        </div>
        <main className="p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
