import {
  Navbar,
  NavbarBrand,
} from "flowbite-react";

export default function NavbarComponent() {
  return (
    <Navbar fluid rounded>
      <NavbarBrand href="https://www.buddhilive.com/">
        <img
          src="/favicon.ico"
          className="mr-3 h-6 sm:h-9"
          alt="Flowbite React Logo"
        />
        <span className="self-center whitespace-nowrap text-xl font-semibold dark:text-white">
          Buddhi
        </span>
      </NavbarBrand>
    </Navbar>
  );
}
