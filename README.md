# MultiSVG Converter and Documentation Website

This project combines documentation, product review, and an SVG-to-G-Code converter in a single web application. The site is structured to promote and explain the features of a multi-functional CNC machine, with sections for product information and interactive SVG conversion.

## Features

- **Product Overview**: Present and promote the multi-functional CNC machine with documentation and feature highlights.
- **SVG to G-Code Converter**: Convert SVG files into multi-layer G-Code with options for different colors and layers, suitable for drilling, drawing, and engraving applications.
- **Multi-Section Layout**: Organized layout with sections for product information, documentation, and the converter tool, all accessible from the header.

## Running the Application

### Prerequisites

- **Docker** and **Docker Compose** should be installed on your system.

### Steps to Run

1. **Start the Application**: Run the following command in the project root to build and start both the Next.js frontend and Flask backend.

    ```bash
    docker-compose up --build
    ```

2. **Access the Site**:
   - The Next.js frontend will be available at [http://localhost:3000](http://localhost:3000).
   - The Flask backend API is configured to run internally within Docker on `http://flask:8080`.

### Project Structure

- **Frontend (Next.js)**: Located in the `nextjs` directory, responsible for the website interface and user interactions.
  - **Pages**:
    - **Home**: Overview of the product features and CNC machine applications.
    - **Documentation**: Detailed product documentation and usage guidelines.
    - **Converter**: Upload SVG files and convert them into multi-layer G-Code.

- **Backend (Flask)**: Located in the `flask` directory, responsible for handling SVG uploads and conversion to G-Code.
  - **Endpoints**:
    - `/api/convert`: Converts SVG files to multi-layer G-Code based on user parameters.
    - `/api/download/<filename>`: Serves downloadable G-Code files as a ZIP archive.

### Configuration

- **Docker Compose**: Configures and runs both services in isolated containers, linked by an internal network.
- **Proxying API Requests**: The Next.js app proxies requests to the Flask API using `/api/` paths, allowing seamless access to backend functionality from the frontend.

### Troubleshooting

- **Port Conflicts**: If a port is in use, update `docker-compose.yml` with available ports.
- **Resource Limits**: If Docker runs out of space, run `docker system prune -a --volumes` to clean up.

### Key Technologies

- **Next.js** for the frontend
- **Flask** for backend processing
- **cairosvg** and **svg_to_gcode** for SVG to G-Code conversion

For additional support or contributions, please open an issue or submit a pull request.
