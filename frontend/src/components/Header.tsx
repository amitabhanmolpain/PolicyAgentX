import { Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/components/ThemeProvider";

const navItems = [
  { path: "/", label: "Home" },
  { path: "/simulate-policy", label: "Simulate" },
  { path: "/compare", label: "Compare" },
  { path: "/history", label: "History" },
];

const Header = () => {
  const location = useLocation();
  const [isScrolled, setIsScrolled] = useState(false);
  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 50) {
        setIsScrolled(true);
      } else {
        setIsScrolled(false);
      }
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className={`app-header-shell fixed z-50 backdrop-blur-md border border-border/60 rounded-2xl shadow-2xl shadow-black/20 transition-all duration-300 ${
        isScrolled 
          ? "top-6 left-[35%] right-[35%] h-16" 
          : "top-4 left-4 right-4 h-20"
      }`}
    >
      <div className="container mx-auto flex items-center justify-center h-full px-8">
        {isScrolled ? (
          <div className="flex items-center justify-between w-full">
            <nav className="flex items-center gap-2">
              {navItems.map((item) => {
                  const isActive = location.pathname === item.path;
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className="relative px-4 py-2 text-xs font-medium transition-all duration-300 group whitespace-nowrap"
                    >
                      <span className={isActive ? "text-foreground" : "text-muted-foreground group-hover:text-foreground"}>
                        {item.label}
                      </span>
                      {isActive && (
                        <motion.div
                          layoutId="activeNav"
                          className="nav-active-indicator absolute -bottom-[17px] left-0 right-0 h-[2px] bg-foreground rounded-t-full"
                          transition={{ type: "spring", stiffness: 380, damping: 30 }}
                        />
                      )}
                    </Link>
                  );
                })}
            </nav>
            <button
              type="button"
              aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
              onClick={toggleTheme}
              className="theme-toggle inline-flex items-center gap-2 rounded-xl border border-border bg-card px-3 py-2 text-xs text-foreground transition hover:bg-secondary"
            >
              {theme === "dark" ? <Sun size={14} /> : <Moon size={14} />}
              {theme === "dark" ? "Light" : "Dark"}
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-between w-full">
            <Link to="/" className="font-display text-xl font-bold text-gradient tracking-tighter">
              PolicyAgentX
            </Link>
            <div className="flex items-center gap-3">
              <nav className="flex items-center gap-2">
                {navItems.map((item) => {
                  const isActive = location.pathname === item.path;
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className="relative px-6 py-2 text-sm font-medium transition-all duration-300 group"
                    >
                      <span className={isActive ? "text-foreground" : "text-muted-foreground group-hover:text-foreground"}>
                        {item.label}
                      </span>
                      {isActive && (
                        <motion.div
                          layoutId="activeNav"
                          className="nav-active-indicator absolute -bottom-[21px] left-0 right-0 h-[2px] bg-foreground rounded-t-full"
                          transition={{ type: "spring", stiffness: 380, damping: 30 }}
                        />
                      )}
                    </Link>
                  );
                })}
              </nav>
              <button
                type="button"
                aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
                onClick={toggleTheme}
                className="theme-toggle inline-flex items-center gap-2 rounded-xl border border-border bg-card px-3 py-2 text-xs text-foreground transition hover:bg-secondary"
              >
                {theme === "dark" ? <Sun size={14} /> : <Moon size={14} />}
                {theme === "dark" ? "Light" : "Dark"}
              </button>
            </div>
          </div>
        )}
      </div>
    </motion.header>
  );
};


export default Header;
