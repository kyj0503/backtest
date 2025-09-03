import React from 'react';
import { Navbar, Nav, Container } from 'react-bootstrap';
import { Link } from 'react-router-dom';

const Header: React.FC = () => {
  return (
    <Navbar bg="primary" variant="dark" expand="lg" sticky="top">
      <Container>
        <Navbar.Brand as={Link} to="/" className="fw-bold">
          📈 백테스팅 플랫폼
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            <Nav.Link as={Link} to="/">
              홈
            </Nav.Link>
            <Nav.Link as={Link} to="/backtest">
              백테스트
            </Nav.Link>
          </Nav>
          <Nav>
            <Nav.Link href="https://github.com/capstone-backtest/backtest" target="_blank">
              <i className="bi bi-github"></i> GitHub
            </Nav.Link>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default Header;
