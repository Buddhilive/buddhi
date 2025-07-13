import {
  Avatar,
  Dropdown,
  DropdownDivider,
  DropdownHeader,
  DropdownItem,
  Navbar,
  NavbarBrand,
  NavbarToggle,
} from "flowbite-react";

export default function Home() {
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
      <div className="flex md:order-2">
        <Dropdown
          arrowIcon={false}
          inline
          label={
            <Avatar
              alt="User settings"
              img="https://www.buddhilive.com/wp-content/uploads/2025/04/Buddhi-Kavindra-Ranasinghe-e1745127102959-300x300.jpg"
              rounded
            />
          }
        >
          <DropdownHeader>
            <span className="block text-sm">Buddhi Kavindra</span>
            <span className="block truncate text-sm font-medium">
              info@buddhilive.com
            </span>
          </DropdownHeader>
          <DropdownItem>Dashboard</DropdownItem>
          <DropdownItem>Settings</DropdownItem>
          <DropdownItem>Earnings</DropdownItem>
          <DropdownDivider />
          <DropdownItem>Sign out</DropdownItem>
        </Dropdown>
        <NavbarToggle />
      </div>
    </Navbar>
  );
}
