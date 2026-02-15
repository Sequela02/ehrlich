import logoUrl from "@/assets/images/logo.svg";

export function InteractiveLogo() {
    return (
        <div className="relative h-24 w-24 cursor-pointer group flex items-center justify-center" title="Ehrlich Engine">
            <img
                src={logoUrl}
                alt="Ehrlich Logo"
                className="h-full w-full object-contain opacity-90 transition-all duration-500 ease-out group-hover:scale-110 group-hover:opacity-100 group-hover:rotate-3"
            />
        </div>
    );
}
