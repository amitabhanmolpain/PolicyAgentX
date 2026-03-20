import { Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";

const navItems = [
  { path: "/", label: "Home" },
  { path: "/simulate-policy", label: "Simulate" },
  { path: "/compare", label: "Compare" },
  { path: "/history", label: "History" },
];

const Header = () => {
  const location = useLocation();

  return (
    <motion.header
      initial={{ y: -80 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="fixed top-0 left-0 right-0 z-50 bg-background/60 backdrop-blur-xl border-b border-border/80 h-20"
    >
      <div className="container mx-auto flex items-center justify-between h-full px-8">
        <Link to="/" className="font-display text-xl font-bold text-gradient tracking-tighter">
          PolicyAgentX
        </Link>
        <nav className="flex items-center gap-2">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className="relative px-6 py-2 text-sm font-medium transition-all duration-300 group"
              >
                <span className={isActive ? "text-white" : "text-muted-foreground group-hover:text-white"}>
                  {item.label}
                </span>
                {isActive && (
                  <motion.div
                    layoutId="activeNav"
                    className="absolute -bottom-[21px] left-0 right-0 h-[2px] bg-white rounded-t-full shadow-[0_-4px_12px_rgba(255,255,255,0.3)]"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
              </Link>
            );
          })}
        </nav>
      </div>
    </motion.header>
  );
};


export default Header;
