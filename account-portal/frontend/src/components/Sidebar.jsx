import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRightIcon, ChevronDownIcon } from "@heroicons/react/24/outline";
import { Link } from "react-router-dom";

export default function Sidebar() {
  const [openMenus, setOpenMenus] = useState({
    provisioning: true,
    server: true,
    sso: true,
    github: true,
    logs: true,
    bedrock: true
  });

  const toggleMenu = (menu) => {
    setOpenMenus(prev => ({ ...prev, [menu]: !prev[menu] }));
  };

  return (
    <div className="w-64 bg-sidebar shadow-lg p-5">
      <div className="mb-6">
        <img src="/logo.svg" alt="목암생명과학연구소" className="w-full" />
      </div>

      <nav className="space-y-3">
        <button
          className="flex items-center justify-between w-full p-2 rounded-lg hover:bg-sidebarHover"
          onClick={() => toggleMenu('provisioning')}
        >
          <span className="font-semibold">통합 프로비저닝</span>
          {openMenus.provisioning ? <ChevronDownIcon className="w-5 h-5" /> : <ChevronRightIcon className="w-5 h-5" />}
        </button>
        <AnimatePresence>
          {openMenus.provisioning && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden ml-5 flex flex-col gap-2"
            >
              <Link to="/provisioning/onboarding" className="p-2 rounded-lg hover:bg-sidebarHover">사용자 등록</Link>
              <Link to="/provisioning/offboarding" className="p-2 rounded-lg hover:bg-sidebarHover">사용자 삭제</Link>
            </motion.div>
          )}
        </AnimatePresence>

        <button
          className="flex items-center justify-between w-full p-2 rounded-lg hover:bg-sidebarHover"
          onClick={() => toggleMenu('server')}
        >
          <span className="font-semibold">서버 계정 관리</span>
          {openMenus.server ? <ChevronDownIcon className="w-5 h-5" /> : <ChevronRightIcon className="w-5 h-5" />}
        </button>
        <AnimatePresence>
          {openMenus.server && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden ml-5 flex flex-col gap-2"
            >
              <Link to="/server/create" className="p-2 rounded-lg hover:bg-sidebarHover">계정 생성</Link>
              <Link to="/server/update" className="p-2 rounded-lg hover:bg-sidebarHover">계정 권한 변경</Link>
              <Link to="/server/delete" className="p-2 rounded-lg hover:bg-sidebarHover">계정 삭제</Link>
              <Link to="/server/project-groups" className="p-2 rounded-lg hover:bg-sidebarHover">계정 프로젝트 권한</Link>
            </motion.div>
          )}
        </AnimatePresence>

        <button
          className="flex items-center justify-between w-full p-2 rounded-lg hover:bg-sidebarHover"
          onClick={() => toggleMenu('sso')}
        >
          <span className="font-semibold">SSO 계정 관리</span>
          {openMenus.sso ? <ChevronDownIcon className="w-5 h-5" /> : <ChevronRightIcon className="w-5 h-5" />}
        </button>
        <AnimatePresence>
          {openMenus.sso && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden ml-5 flex flex-col gap-2"
            >
              <Link to="/sso/permission" className="p-2 rounded-lg hover:bg-sidebarHover">ROLE 권한 변경</Link>
            </motion.div>
          )}
        </AnimatePresence>

        <button
          className="flex items-center justify-between w-full p-2 rounded-lg hover:bg-sidebarHover"
          onClick={() => toggleMenu('github')}
        >
          <span className="font-semibold">GitHub 관리</span>
          {openMenus.github ? <ChevronDownIcon className="w-5 h-5" /> : <ChevronRightIcon className="w-5 h-5" />}
        </button>
        <AnimatePresence>
          {openMenus.github && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden ml-5 flex flex-col gap-2"
            >
              <Link to="/github/permissions" className="p-2 rounded-lg hover:bg-sidebarHover">저장소 프로젝트 권한</Link>
            </motion.div>
          )}
        </AnimatePresence>

        <button
          className="flex items-center justify-between w-full p-2 rounded-lg hover:bg-sidebarHover"
          onClick={() => toggleMenu('logs')}
        >
          <span className="font-semibold">모니터링</span>
          {openMenus.logs ? <ChevronDownIcon className="w-5 h-5" /> : <ChevronRightIcon className="w-5 h-5" />}
        </button>
        <AnimatePresence>
          {openMenus.logs && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden ml-5 flex flex-col gap-2"
            >
              <Link to="/logs" className="p-2 rounded-lg hover:bg-sidebarHover">포털 작업 로그</Link>
              <Link to="/user-logs" className="p-2 rounded-lg hover:bg-sidebarHover">사용자 접속 로그</Link>
              <Link to="/github-audit" className="p-2 rounded-lg hover:bg-sidebarHover">GitHub 로그</Link>
            </motion.div>
          )}
        </AnimatePresence>

        <button
          className="flex items-center justify-between w-full p-2 rounded-lg hover:bg-sidebarHover"
          onClick={() => toggleMenu('bedrock')}
        >
          <span className="font-semibold">Bedrock 게이트웨이</span>
          {openMenus.bedrock ? <ChevronDownIcon className="w-5 h-5" /> : <ChevronRightIcon className="w-5 h-5" />}
        </button>
        <AnimatePresence>
          {openMenus.bedrock && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden ml-5 flex flex-col gap-2"
            >
              <Link to="/bedrock-gateway" className="p-2 rounded-lg hover:bg-sidebarHover">사용량 모니터링</Link>
            </motion.div>
          )}
        </AnimatePresence>
      </nav>
    </div>
  );
}
