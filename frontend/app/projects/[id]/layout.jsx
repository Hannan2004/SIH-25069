import ProjectSidebar from "@/components/ProjectSidebar";

export default function ProjectLayout({ children }) {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-10">
        <div className="lg:col-span-1 order-last lg:order-first">
          <ProjectSidebar />
        </div>
        <div className="lg:col-span-4">{children}</div>
      </div>
    </div>
  );
}
