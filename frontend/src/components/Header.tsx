import { Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { useState, useEffect } from "react";

const navItems = [
  { path: "/", label: "Home" },
  { path: "/simulate-policy", label: "Simulate" },
  { path: "/compare", label: "Compare" },
  { path: "/history", label: "History" },
];

const Header = () => {
  const location = useLocation();
  const [isScrolled, setIsScrolled] = useState(false);

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
      className={`fixed z-50 bg-background/80 backdrop-blur-md border border-border/60 rounded-2xl shadow-2xl shadow-black/20 transition-all duration-300 ${
        isScrolled 
          ? "top-6 left-[35%] right-[35%] h-16" 
          : "top-4 left-4 right-4 h-20"
      }`}
    >
      <div className="container mx-auto flex items-center justify-center h-full px-8">
        {isScrolled ? (
          <nav className="flex items-center gap-2">
            {navItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className="relative px-4 py-2 text-xs font-medium transition-all duration-300 group whitespace-nowrap"
                  >
                    <span className={isActive ? "text-white" : "text-muted-foreground group-hover:text-white"}>
                      {item.label}
                    </span>
                    {isActive && (
                      <motion.div
                        layoutId="activeNav"
                        className="absolute -bottom-[17px] left-0 right-0 h-[2px] bg-white rounded-t-full shadow-[0_-4px_12px_rgba(255,255,255,0.3)]"
                        transition={{ type: "spring", stiffness: 380, damping: 30 }}
                      />
                    )}
                  </Link>
                );
              })}
          </nav>
        ) : (
          <div className="flex items-center justify-between w-full">
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
        )}
      </div>
    </motion.header>
  );
};


export default Header;
