const Footer = () => (
  <footer className="border-t border-border/80 py-12 mt-auto bg-background">
    <div className="container mx-auto px-8 text-center flex flex-col items-center gap-4">
      <div className="h-[1px] w-20 bg-gradient-to-r from-transparent via-accent/30 to-transparent" />
      <p className="text-xs text-muted-foreground uppercase tracking-[0.2em] font-medium">
        PolicyAgentX <span className="mx-2 opacity-30">|</span> <span className="opacity-60 text-[10px]">Simulate. Analyze. Decide.</span>
      </p>
      <p className="text-[10px] text-muted-foreground/40 mt-1">
        &copy; {new Date().getFullYear()} Advanced Policy Simulation Systems.
      </p>
    </div>
  </footer>
);


export default Footer;
